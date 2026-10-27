# -*- coding: utf-8 -*-
"""手机浏览器版计算引擎（在 Pyodide 里运行的 SymPy）。

与 solver.py 功能一致，但去掉了 parse_latex（避免依赖 antlr），
只保留 parse_expr（支持 ^ 幂、sin(x)、隐式乘法）。返回 JSON 友好 dict。
"""
import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor,
)

x, y, z, t, n = sp.symbols("x y z t n")
_TR = standard_transformations + (implicit_multiplication_application, convert_xor)
_CJK = re.compile(r"[㐀-䶿一-鿿]")
_PT = {"inf": sp.oo, "infinity": sp.oo, "+inf": sp.oo, "-inf": -sp.oo, "oo": sp.oo,
       "∞": sp.oo, "+∞": sp.oo, "-∞": -sp.oo}


def _pe(s):
    s = s.strip()
    if _CJK.search(s):
        raise ValueError("包含中文，不是可计算的式子")
    return parse_expr(s, transformations=_TR)


def _pp(s):
    s = s.strip()
    return _PT.get(s, _pe(s))


def _split_eq(rest):
    eqs = []
    for p in re.split(r"[,;；\n]+", rest):
        p = p.strip()
        if not p:
            continue
        if "=" in p:
            l, r = p.split("=", 1)
            eqs.append(sp.Eq(_pe(l), _pe(r), evaluate=False))
        else:
            eqs.append(sp.Eq(_pe(p), 0, evaluate=False))
    return eqs


def _fmt_sol(sol):
    if sol is None:
        return r"\varnothing", "无解"
    if sol == sp.EmptySet:
        return r"\varnothing", "无解（空集）"
    if isinstance(sol, sp.ConditionSet):
        return r"\text{no closed-form solution}", "无初等闭式解"
    if isinstance(sol, (sp.FiniteSet, sp.ImageSet)):
        return sp.latex(sol), None
    if isinstance(sol, dict):
        return ", ".join(f"{sp.latex(k)}={sp.latex(v)}" for k, v in sol.items()), None
    if isinstance(sol, (list, tuple)):
        if sol and all(isinstance(s, dict) for s in sol):
            return ";  ".join(
                ", ".join(f"{sp.latex(k)}={sp.latex(v)}" for k, v in s.items()) for s in sol
            ), None
        if sol:
            return ", ".join(sp.latex(s) for s in sol), None
        return r"\varnothing", "无解"
    return sp.latex(sol), None


def _payload(interp, res):
    out = {"interpreted": interp, "result": sp.latex(res), "plain": str(res)}
    try:
        if not res.free_symbols:
            out["approx"] = str(res.evalf(6))
    except Exception:
        pass
    return out


def solve_cmd(rest):
    eqs = _split_eq(rest)
    interp = " ;  ".join(f"{sp.latex(e.lhs)}={sp.latex(e.rhs)}" for e in eqs)
    if len(eqs) == 1:
        eq = eqs[0]
        syms = list(eq.free_symbols)
        if not syms:
            if sp.simplify(eq.lhs - eq.rhs) == 0:
                return {"interpreted": interp, "result": r"\text{identity: true for all values}",
                        "plain": "恒等式", "note": "恒等式，对任意取值成立"}
            return {"interpreted": interp, "result": r"\text{contradiction}",
                    "plain": "矛盾", "note": "矛盾，无解"}
        if len(syms) == 1:
            sol = sp.solveset(eq, syms[0])
            if isinstance(sol, sp.ConditionSet):
                sol = sp.solve(eq, syms[0])
        else:
            sol = sp.solve(eq, dict=True)
    else:
        sol = sp.solve(eqs, dict=True)
    result, note = _fmt_sol(sol)
    out = {"interpreted": interp, "result": result, "plain": str(sol)}
    if note:
        out["note"] = note
    return out


def diff_cmd(rest):
    rest = rest.strip().strip("[]")
    parts = [p.strip() for p in rest.split(",")]
    expr = _pe(parts[0])
    var = sp.Symbol(parts[1]) if len(parts) >= 2 else x
    order = int(parts[2]) if len(parts) >= 3 else 1
    if order == 1:
        interp = f"\\frac{{d}}{{d{sp.latex(var)}}}\\left({sp.latex(expr)}\\right)"
    else:
        interp = f"\\frac{{d^{{{order}}}}}{{d{sp.latex(var)}^{{{order}}}}}\\left({sp.latex(expr)}\\right)"
    return _payload(interp, sp.diff(expr, var, order))


def integrate_cmd(rest):
    rest = re.sub(r"\s*d\s*[a-zA-Z]\s*$", "", rest.strip())
    rest = rest.strip().rstrip(",")
    m = re.search(r"\bfrom\s+([^\s]+)\s+to\s+([^\s]+)\s*$", rest)
    if m:
        expr = _pe(rest[:m.start()].strip().rstrip(",;，； "))
        a, b = _pp(m.group(1)), _pp(m.group(2))
        res = sp.integrate(expr, (x, a, b))
        return _payload(f"\\int_{{{sp.latex(a)}}}^{{{sp.latex(b)}}} {sp.latex(expr)} \\, dx", res)
    parts = [p.strip() for p in rest.split(",")]
    expr = _pe(parts[0])
    if len(parts) >= 3:
        a, b = _pp(parts[-2]), _pp(parts[-1])
        var = sp.Symbol(parts[1]) if len(parts) == 4 else x
        res = sp.integrate(expr, (var, a, b))
        return _payload(f"\\int_{{{sp.latex(a)}}}^{{{sp.latex(b)}}} {sp.latex(expr)} \\, d{sp.latex(var)}", res)
    var = sp.Symbol(parts[1]) if len(parts) == 2 else x
    res = sp.integrate(expr, var)
    out = _payload(f"\\int {sp.latex(expr)} \\, d{sp.latex(var)}", res)
    if isinstance(res, sp.Integral):
        out["note"] = "该积分无初等原函数"
    return out


def limit_cmd(rest):
    rest = rest.strip()
    m = re.search(r"([a-zA-Z]\w*)\s*->\s*([^\s,]+)", rest)
    if m:
        var = sp.Symbol(m.group(1))
        pt = _pp(m.group(2))
        et = re.sub(r"\s*(as|当|趋近于|趋于|趋近|趋)\s*$", "", rest[:m.start()].strip(), flags=re.I).strip().rstrip(",;，； ")
        expr = _pe(et)
        res = sp.limit(expr, var, pt)
        return _payload(f"\\lim_{{{sp.latex(var)}\\to {sp.latex(pt)}}} {sp.latex(expr)}", res)
    parts = [p.strip() for p in rest.split(",")]
    expr = _pe(parts[0])
    var = sp.Symbol(parts[1]) if len(parts) >= 3 else x
    pt = _pp(parts[2]) if len(parts) >= 3 else 0
    res = sp.limit(expr, var, pt)
    return _payload(f"\\lim_{{{sp.latex(var)}\\to {sp.latex(pt)}}} {sp.latex(expr)}", res)


def series_cmd(rest):
    rest = rest.strip()
    m = re.search(r"\bat\s+([a-zA-Z]\w*)\s*=\s*([^\s,]+)", rest)
    if m:
        expr = _pe(rest[:m.start()].strip().rstrip(",;，； "))
        var, pt = sp.Symbol(m.group(1)), _pp(m.group(2))
        res = sp.series(expr, var, pt, 6)
        return _payload(f"\\text{{series of }} {sp.latex(expr)} \\text{{ at }} {sp.latex(var)}={sp.latex(pt)}", res)
    parts = [p for p in re.split(r"[,\s]+", rest.strip()) if p]
    expr = _pe(parts[0])
    var = sp.Symbol(parts[1]) if len(parts) >= 2 else x
    pt = _pp(parts[2]) if len(parts) >= 3 else 0
    order = int(parts[3]) if len(parts) >= 4 else 6
    res = sp.series(expr, var, pt, order)
    return _payload(f"\\text{{series of }} {sp.latex(expr)} \\text{{ at }} {sp.latex(var)}={sp.latex(pt)}", res)


def simple_cmd(rest):
    return _payload(sp.latex(_pe(rest)), sp.simplify(_pe(rest)))


def factor_cmd(rest):
    return _payload(sp.latex(_pe(rest)), sp.factor(_pe(rest)))


def expand_cmd(rest):
    return _payload(sp.latex(_pe(rest)), sp.expand(_pe(rest)))


def dsolve_cmd(rest):
    f = sp.Function("f")
    rest = rest.strip()
    if "=" in rest:
        l, r = rest.split("=", 1)
        eq = sp.Eq(parse_expr(l, local_dict={"f": f}), parse_expr(r, local_dict={"f": f}))
    else:
        eq = parse_expr(rest, local_dict={"f": f})
    sol = sp.dsolve(eq, f(x))
    res = ";  ".join(sp.latex(s) for s in sol) if isinstance(sol, list) else sp.latex(sol)
    return {"interpreted": sp.latex(eq), "result": res, "plain": str(sol)}


def _mat(rest):
    s = rest.strip()
    if not s.startswith("[["):
        raise ValueError("矩阵请写成 [[a,b],[c,d]]")
    inner = s[1:-1].strip()
    rows = []
    depth = 0
    cur = ""
    for ch in inner:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            rows.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        rows.append(cur)
    data = []
    for r in rows:
        r = r.strip()
        if r.startswith("["):
            r = r[1:]
        if r.endswith("]"):
            r = r[:-1]
        ent = [e.strip() for e in r.split(",") if e.strip()]
        if ent:
            data.append([_pe(e) for e in ent])
    return sp.Matrix(data)


def eigenvals_cmd(rest):
    M = _mat(rest)
    ev = M.eigenvals()
    parts = [f"\\lambda = {sp.latex(v)} \\;(\\text{{mult }}{m}\\text{{)}}" for v, m in ev.items()]
    return {"interpreted": sp.latex(M), "result": " ,  ".join(parts), "plain": str(ev)}


def det_cmd(rest):
    M = _mat(rest)
    return _payload(sp.latex(M), M.det())


def inv_cmd(rest):
    M = _mat(rest)
    if M.det() == 0:
        return {"interpreted": sp.latex(M), "result": r"\text{singular (det}=0\text{)}",
                "plain": "不可逆", "note": "矩阵不可逆（行列式为 0）"}
    return {"interpreted": sp.latex(M), "result": sp.latex(M.inv()), "plain": str(M.inv())}


def rank_cmd(rest):
    M = _mat(rest)
    return {"interpreted": sp.latex(M), "result": sp.latex(M.rank()), "plain": str(M.rank())}


def _toint(rest):
    rest = rest.strip()
    if rest.isdigit():
        return int(rest)
    v = _pe(rest)
    iv = int(v)
    if iv != v:
        raise ValueError("需要整数")
    return iv


def factorint_cmd(rest):
    n = _toint(rest)
    d = sp.factorint(n)
    if not d:
        return {"interpreted": f"\\text{{factorint}}({n})", "result": "1", "plain": "1",
                "note": "1 既非素数也非合数"}
    parts = [f"{sp.latex(p)}^{{{e}}}" if e > 1 else f"{sp.latex(p)}" for p, e in sorted(d.items())]
    return {"interpreted": f"\\text{{factorint}}({n})", "result": " \\times ".join(parts), "plain": str(d)}


def isprime_cmd(rest):
    n = _toint(rest)
    p = sp.isprime(n)
    return {"interpreted": f"\\text{{isprime}}({n})", "result": r"\text{prime}" if p else r"\text{not prime}",
            "plain": str(p), "note": "是素数" if p else "不是素数"}


def totient_cmd(rest):
    n = _toint(rest)
    return {"interpreted": f"\\varphi({n})", "result": sp.latex(sp.totient(n)), "plain": str(sp.totient(n))}


def gcd_cmd(rest):
    parts = [p for p in re.split(r"[,\s]+", rest.strip()) if p]
    if len(parts) < 2:
        raise ValueError("gcd 需要两个数，如 gcd 12 18")
    a, b = _pe(parts[0]), _pe(parts[1])
    return {"interpreted": f"\\gcd({sp.latex(a)},{sp.latex(b)})",
            "result": sp.latex(sp.gcd(a, b)), "plain": str(sp.gcd(a, b))}


_CMDS = [
    ("dsolve", ["微分方程", "dsolve"]),
    ("integrate", ["积分", "integrate", "integral", "∫"]),
    ("diff", ["求导", "导数", "微分", "diff", "derivative", "d/dx"]),
    ("limit", ["极限", "limit"]),
    ("solve", ["解方程组", "解方程", "求解", "solve", "方程"]),
    ("series", ["泰勒展开", "级数展开", "泰勒", "taylor", "series"]),
    ("eigenvals", ["特征值", "eigenvalues", "eigenvals"]),
    ("det", ["行列式", "det", "determinant"]),
    ("inv", ["逆矩阵", "inverse"]),
    ("rank", ["秩", "rank"]),
    ("factorint", ["质因数分解", "factorint"]),
    ("isprime", ["素数判断", "isprime"]),
    ("totient", ["欧拉函数", "totient"]),
    ("gcd", ["最大公约数", "gcd"]),
    ("factor", ["因式分解", "分解因式", "factor"]),
    ("expand", ["展开", "expand"]),
    ("simplify", ["化简", "simplify"]),
]

_HANDLERS = {
    "solve": solve_cmd, "diff": diff_cmd, "integrate": integrate_cmd, "limit": limit_cmd,
    "series": series_cmd, "simplify": simple_cmd, "factor": factor_cmd, "expand": expand_cmd,
    "dsolve": dsolve_cmd, "eigenvals": eigenvals_cmd, "det": det_cmd, "inv": inv_cmd,
    "rank": rank_cmd, "factorint": factorint_cmd, "isprime": isprime_cmd,
    "totient": totient_cmd, "gcd": gcd_cmd,
}


def _detect(q):
    low = q.lower()
    for cmd, kws in _CMDS:
        for kw in kws:
            i = low.find(kw)
            if i != -1:
                return cmd, q[i + len(kw):].strip().lstrip(":：,， =")
    return None, q


def compute(q):
    q = (q or "").strip()
    if not q:
        return {"ok": False, "error": "请输入数学问题"}
    cmd = None
    try:
        cmd, rest = _detect(q)
        if cmd is None and "=" in q:
            cmd, rest = "solve", q
        elif cmd is None:
            expr = _pe(q)
            res = sp.simplify(expr)
            out = {"interpreted": sp.latex(expr), "result": sp.latex(res), "plain": str(res)}
            try:
                if not res.free_symbols:
                    out["approx"] = str(res.evalf(6))
            except Exception:
                pass
            try:
                fac = sp.factor(expr)
                if sp.latex(fac) != sp.latex(res):
                    out["factor"] = sp.latex(fac)
            except Exception:
                pass
            out["ok"] = True
            out["type"] = "evaluate"
            return out
        r = _HANDLERS[cmd](rest)
        r["ok"] = True
        r["type"] = cmd
        return r
    except Exception as e:
        return {"ok": False, "error": str(e), "type": cmd or "parse"}
