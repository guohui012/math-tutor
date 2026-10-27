# -*- coding: utf-8 -*-
"""严谨的数学计算引擎（SymPy 符号计算）。

设计原则：
- 只返回解析解（精确值）；数值近似仅作旁证，绝不输出"AI 猜的答案"。
- 每次计算都返回"输入理解"（interpreted），供用户核验软件没有误解题目。
- 计算失败时给出明确错误，而不是含糊兜底。
"""
import re

from sympy import (
    Symbol, symbols, Function, Eq, simplify, factor, expand, diff,
    integrate, limit, solve, solveset, dsolve, series, latex,
    oo, pi, E, I, Matrix, gcd, factorint, isprime, totient,
    ConditionSet, EmptySet, FiniteSet, ImageSet,
    Integral, Derivative, Limit,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor,
)
from sympy.parsing.latex import parse_latex

x, y, z, t, n = symbols("x y z t n")

_TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)

_POINT_ALIASES = {
    "inf": oo, "infinity": oo, "+inf": oo, "-inf": -oo,
    "∞": oo, "+∞": oo, "-∞": -oo, "oo": oo,
}


_CJK = re.compile(r"[㐀-䶿一-鿿]")


def parse_expression(text):
    """解析输入为 SymPy 表达式；Python 风格优先，LaTeX 兜底。

    含中文的输入（如"证明 √2 是无理数"）不是可计算的式子，
    直接判为解析失败，交给讲解引擎处理，避免被隐式乘法当成字符相乘。
    """
    text = text.strip()
    if _CJK.search(text):
        raise ValueError("输入含中文，不是可计算的式子。概念/证明题请点“只讲原理”；计算请用符号写法（x^2、sin(x)、from 0 to 1）。")
    errs = []
    if "\\" in text:  # 明确是 LaTeX
        try:
            return parse_latex(text)
        except Exception as e:
            errs.append(f"LaTeX: {e}")
    try:
        return parse_expr(text, transformations=_TRANSFORMS)
    except Exception as e:
        errs.append(f"表达式: {e}")
    try:
        return parse_latex(text)
    except Exception as e:
        errs.append(f"LaTeX: {e}")
    raise ValueError("无法解析「%s」\n%s" % (text, "\n".join(errs)))


def parse_point(s):
    s = s.strip()
    if s in _POINT_ALIASES:
        return _POINT_ALIASES[s]
    return parse_expression(s)


_COMMANDS = [
    ("dsolve",      ["微分方程", "dsolve"]),
    ("series",      ["泰勒展开", "级数展开", "泰勒", "taylor", "series"]),
    ("integrate",   ["积分", "integrate", "integral", "∫", "\\int"]),
    ("diff",        ["求导", "导数", "微分", "diff", "derivative", "d/dx", "\\frac{d}{dx}"]),
    ("limit",       ["极限", "limit", "\\lim"]),
    ("solve",       ["解方程组", "解方程", "求解", "solve", "方程"]),
    ("eigenvects",  ["特征向量", "eigenvectors", "eigenvects"]),
    ("eigenvals",   ["特征值", "eigenvalues", "eigenvals"]),
    ("det",         ["行列式", "det", "determinant"]),
    ("inv",         ["逆矩阵", "inverse"]),
    ("rank",        ["秩", "rank"]),
    ("rref",        ["行最简", "rref"]),
    ("factorint",   ["质因数分解", "factorint"]),
    ("isprime",     ["素数判断", "isprime"]),
    ("totient",     ["欧拉函数", "totient"]),
    ("gcd",         ["最大公约数", "gcd"]),
    ("factor",      ["因式分解", "分解因式", "factor"]),
    ("expand",      ["展开", "expand"]),
    ("simplify",    ["化简", "simplify"]),
]


def detect_command(q):
    low = q.lower()
    for cmd, kws in _COMMANDS:
        for kw in kws:
            i = low.find(kw)
            if i != -1:
                rest = q[i + len(kw):].strip()
                rest = rest.lstrip(":：,， =")
                return cmd, rest
    return None, q


def _split_eq(rest):
    """把输入拆成 Eq 列表（方程组用 , ; ； 换行 分隔）。

    用 evaluate=False 避免常量方程（如 0=0、1=2）被 SymPy 自动化简成布尔值，
    从而保持 .lhs/.rhs 可用，交给 solve_cmd 判定恒等式/矛盾。
    """
    parts = re.split(r"[,;；\n]+", rest)
    eqs = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if "=" in p:
            lhs, rhs = p.split("=", 1)
            eqs.append(Eq(parse_expression(lhs), parse_expression(rhs), evaluate=False))
        else:
            eqs.append(Eq(parse_expression(p), 0, evaluate=False))
    return eqs


def format_solutions(sol):
    """返回 (latex结果, 中文备注或 None)。结果必须是 KaTeX 可渲染的纯 LaTeX。"""
    if sol is None:
        return r"\varnothing", "无解"
    if sol == EmptySet:
        return r"\varnothing", "无解（空集）"
    if isinstance(sol, ConditionSet):
        return r"\text{no closed-form solution}", "无初等闭式解"
    if isinstance(sol, (FiniteSet, ImageSet)):
        return latex(sol), None
    if isinstance(sol, dict):
        parts = [f"{latex(k)} = {latex(v)}" for k, v in sol.items()]
        return ", ".join(parts), None
    if isinstance(sol, (list, tuple)):
        if sol and all(isinstance(s, dict) for s in sol):
            parts = []
            for s in sol:
                parts.append(", ".join(f"{latex(k)} = {latex(v)}" for k, v in s.items()))
            return ";  ".join(parts), None
        if sol:
            return ", ".join(latex(s) for s in sol), None
        return r"\varnothing", "无解"
    return latex(sol), None


def _payload(interpreted, result):
    """构造统一返回结构；结果为常量时附数值近似。"""
    out = {"interpreted": interpreted, "result": latex(result), "plain": str(result)}
    try:
        if not result.free_symbols:
            out["approx"] = str(result.evalf(6))
    except Exception:
        pass
    return out


def solve_cmd(rest):
    eqs = _split_eq(rest)
    interpreted = " ;  ".join(f"{latex(e.lhs)} = {latex(e.rhs)}" for e in eqs)
    if len(eqs) == 1:
        eq = eqs[0]
        syms = list(eq.free_symbols)
        if not syms:
            if simplify(eq.lhs - eq.rhs) == 0:
                return {"interpreted": interpreted, "result": r"\text{identity: true for all values}", "plain": "恒等式", "note": "恒等式，对任意取值成立"}
            return {"interpreted": interpreted, "result": r"\text{contradiction}", "plain": "矛盾", "note": "矛盾，无解"}
        if len(syms) == 1:
            s = syms[0]
            sol = solveset(eq, s)
            if isinstance(sol, ConditionSet):
                sol = solve(eq, s)
        else:
            sol = solve(eq, dict=True)
    else:
        sol = solve(eqs, dict=True)
    result, note = format_solutions(sol)
    out = {"interpreted": interpreted, "result": result, "plain": str(sol)}
    if note:
        out["note"] = note
    return out


def diff_cmd(rest):
    rest = rest.strip().strip("[]")
    parts = [p.strip() for p in rest.split(",")]
    expr = parse_expression(parts[0])
    var = Symbol(parts[1]) if len(parts) >= 2 else x
    order = int(parts[2]) if len(parts) >= 3 else 1
    if order == 1:
        interpreted = f"\\frac{{d}}{{d{latex(var)}}}\\left({latex(expr)}\\right)"
    else:
        interpreted = f"\\frac{{d^{{{order}}}}}{{d{latex(var)}^{{{order}}}}}\\left({latex(expr)}\\right)"
    result = diff(expr, var, order)
    return _payload(interpreted, result)


def integrate_cmd(rest):
    rest = rest.strip()
    rest = re.sub(r"\s*d\s*[a-zA-Z]\s*$", "", rest)
    rest = rest.strip().rstrip(",")
    m = re.search(r"\bfrom\s+([^\s]+)\s+to\s+([^\s]+)\s*$", rest)
    if m:
        expr_text = rest[:m.start()].strip().rstrip(",;，； ")
        expr = parse_expression(expr_text)
        a = parse_point(m.group(1))
        b = parse_point(m.group(2))
        result = integrate(expr, (x, a, b))
        interp = f"\\int_{{{latex(a)}}}^{{{latex(b)}}} {latex(expr)} \\, d{latex(x)}"
        return _payload(interp, result)
    parts = [p.strip() for p in rest.split(",")]
    expr = parse_expression(parts[0])
    if len(parts) >= 3:
        a = parse_point(parts[-2])
        b = parse_point(parts[-1])
        var = Symbol(parts[1]) if len(parts) == 4 else x
        result = integrate(expr, (var, a, b))
        interp = f"\\int_{{{latex(a)}}}^{{{latex(b)}}} {latex(expr)} \\, d{latex(var)}"
        return _payload(interp, result)
    if len(parts) == 2:
        var = Symbol(parts[1])
        result = integrate(expr, var)
    else:
        var = x
        result = integrate(expr, x)
    interp = f"\\int {latex(expr)} \\, d{latex(var)}"
    out = _payload(interp, result)
    if isinstance(result, Integral):
        out["note"] = "该积分无初等原函数（符号引擎未能求出解析解）。"
    return out


def limit_cmd(rest):
    rest = rest.strip()
    m = re.search(r"([a-zA-Z]\w*)\s*->\s*([^\s,]+)", rest)
    if m:
        var = Symbol(m.group(1))
        pt = parse_point(m.group(2))
        expr_text = rest[:m.start()].strip()
        expr_text = re.sub(r"\s*(as|当|趋近于|趋于|趋近|趋|approaches)\s*$", "", expr_text, flags=re.I)
        expr_text = expr_text.strip().rstrip(",;，； ")
        expr = parse_expression(expr_text)
        result = limit(expr, var, pt)
        interp = f"\\lim_{{{latex(var)}\\to {latex(pt)}}} {latex(expr)}"
        return _payload(interp, result)
    parts = [p.strip() for p in rest.split(",")]
    expr = parse_expression(parts[0])
    if len(parts) >= 3:
        var = Symbol(parts[1])
        pt = parse_point(parts[2])
    else:
        var = x
        pt = 0
    result = limit(expr, var, pt)
    interp = f"\\lim_{{{latex(var)}\\to {latex(pt)}}} {latex(expr)}"
    return _payload(interp, result)


def series_cmd(rest):
    rest = rest.strip()
    m = re.search(r"\bat\s+([a-zA-Z]\w*)\s*=\s*([^\s,]+)", rest)
    if m:
        expr_text = rest[:m.start()].strip().rstrip(",;，； ")
        expr = parse_expression(expr_text)
        var = Symbol(m.group(1))
        pt = parse_point(m.group(2))
        result = series(expr, var, pt, 6)
        interp = f"\\text{{series of }} {latex(expr)} \\text{{ at }} {latex(var)}={latex(pt)}"
        return _payload(interp, result)
    parts = [p for p in re.split(r"[,\s]+", rest.strip()) if p]
    expr = parse_expression(parts[0])
    var = Symbol(parts[1]) if len(parts) >= 2 else x
    pt = parse_point(parts[2]) if len(parts) >= 3 else 0
    order = int(parts[3]) if len(parts) >= 4 else 6
    result = series(expr, var, pt, order)
    interp = f"{latex(expr)} \\;\\text{{在}}\\; {latex(var)}={latex(pt)} \\;\\text{{处展开}}"
    return _payload(interp, result)


def simplify_cmd(rest):
    expr = parse_expression(rest)
    return _payload(latex(expr), simplify(expr))


def factor_cmd(rest):
    expr = parse_expression(rest)
    return _payload(latex(expr), factor(expr))


def expand_cmd(rest):
    expr = parse_expression(rest)
    return _payload(latex(expr), expand(expr))


def dsolve_cmd(rest):
    f = Function("f")
    local = {"f": f}
    rest = rest.strip()
    if "=" in rest:
        lhs, rhs = rest.split("=", 1)
        eq = Eq(parse_expr(lhs, local_dict=local), parse_expr(rhs, local_dict=local))
    else:
        eq = parse_expr(rest, local_dict=local)
    sol = dsolve(eq, f(x))
    if isinstance(sol, list):
        result = ";  ".join(latex(s) for s in sol)
    else:
        result = latex(sol)
    return {"interpreted": latex(eq), "result": result, "plain": str(sol)}


def _expr_result(expr):
    simp = simplify(expr)
    out = {"interpreted": latex(expr), "result": latex(simp), "plain": str(simp)}
    try:
        if not simp.free_symbols:
            out["approx"] = str(simp.evalf(6))
    except Exception:
        pass
    try:
        fac = factor(expr)
        if latex(fac) != latex(simp):
            out["factor"] = latex(fac)
    except Exception:
        pass
    return out


def evaluate_cmd(rest):
    if "\\" in rest:
        try:
            obj = parse_latex(rest)
        except Exception:
            obj = None
        if isinstance(obj, (Integral, Derivative, Limit)):
            result = obj.doit()
            return _payload(latex(obj), result)
        if obj is not None:
            return _expr_result(obj)
    expr = parse_expression(rest)
    return _expr_result(expr)


def _parse_matrix(s):
    s = s.strip()
    if not s.startswith("[["):
        raise ValueError("矩阵请写成 [[a,b],[c,d]] 形式（每行一对中括号）。")
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
        entries = [e.strip() for e in r.split(",") if e.strip()]
        if entries:
            data.append([parse_expression(e) for e in entries])
    if not data:
        raise ValueError("矩阵为空。")
    return Matrix(data)


def _to_int(rest):
    rest = rest.strip()
    if rest.isdigit():
        return int(rest)
    v = parse_expression(rest)
    iv = int(v)
    if iv != v:
        raise ValueError("需要整数。")
    return iv


def eigenvals_cmd(rest):
    M = _parse_matrix(rest)
    ev = M.eigenvals()
    parts = [f"\\lambda = {latex(v)} \\;(\\text{{mult }}{m}\\text{{)}}" for v, m in ev.items()]
    return {"interpreted": latex(M), "result": " ,  ".join(parts), "plain": str(ev)}


def eigenvects_cmd(rest):
    M = _parse_matrix(rest)
    out = []
    for v, m, vecs in M.eigenvects():
        for vec in vecs:
            out.append(f"\\lambda = {latex(v)}: {latex(vec)}")
    return {"interpreted": latex(M), "result": " ;  ".join(out) if out else "无", "plain": str(M.eigenvects())}


def det_cmd(rest):
    M = _parse_matrix(rest)
    return _payload(latex(M), M.det())


def inv_cmd(rest):
    M = _parse_matrix(rest)
    if M.det() == 0:
        return {"interpreted": latex(M), "result": r"\text{singular (det} = 0\text{)}", "plain": "不可逆", "note": "矩阵不可逆（行列式为 0）"}
    return {"interpreted": latex(M), "result": latex(M.inv()), "plain": str(M.inv())}


def rank_cmd(rest):
    M = _parse_matrix(rest)
    return {"interpreted": latex(M), "result": latex(M.rank()), "plain": str(M.rank())}


def rref_cmd(rest):
    M = _parse_matrix(rest)
    rr, _ = M.rref()
    return {"interpreted": latex(M), "result": latex(rr), "plain": str(rr)}


def factorint_cmd(rest):
    n = _to_int(rest)
    d = factorint(n)
    if not d:
        return {"interpreted": f"\\text{{factorint}}({n})", "result": "1", "plain": "1", "note": "1 既非素数也非合数"}
    parts = [f"{latex(p)}^{{{e}}}" if e > 1 else f"{latex(p)}" for p, e in sorted(d.items())]
    return {"interpreted": f"\\text{{factorint}}({n})", "result": " \\times ".join(parts), "plain": str(d)}


def isprime_cmd(rest):
    n = _to_int(rest)
    p = isprime(n)
    return {"interpreted": f"\\text{{isprime}}({n})", "result": r"\text{prime}" if p else r"\text{not prime}", "plain": str(p), "note": "是素数" if p else "不是素数"}


def totient_cmd(rest):
    n = _to_int(rest)
    return {"interpreted": f"\\varphi({n})", "result": latex(totient(n)), "plain": str(totient(n))}


def gcd_cmd(rest):
    parts = [p for p in re.split(r"[,\s]+", rest.strip()) if p]
    if len(parts) < 2:
        raise ValueError("gcd 需要两个数，如 gcd 12 18")
    a = parse_expression(parts[0])
    b = parse_expression(parts[1])
    return {"interpreted": f"\\gcd({latex(a)}, {latex(b)})", "result": latex(gcd(a, b)), "plain": str(gcd(a, b))}


HANDLERS = {
    "solve": solve_cmd,
    "diff": diff_cmd,
    "integrate": integrate_cmd,
    "limit": limit_cmd,
    "series": series_cmd,
    "simplify": simplify_cmd,
    "factor": factor_cmd,
    "expand": expand_cmd,
    "dsolve": dsolve_cmd,
    "eigenvals": eigenvals_cmd,
    "eigenvects": eigenvects_cmd,
    "det": det_cmd,
    "inv": inv_cmd,
    "rank": rank_cmd,
    "rref": rref_cmd,
    "factorint": factorint_cmd,
    "isprime": isprime_cmd,
    "totient": totient_cmd,
    "gcd": gcd_cmd,
    "evaluate": evaluate_cmd,
}


def compute(query):
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "请输入数学问题。"}
    cmd = None
    try:
        cmd, rest = detect_command(q)
        if cmd is None and "=" in q:
            cmd, rest = "solve", q
        elif cmd is None:
            cmd, rest = "evaluate", q
        res = HANDLERS[cmd](rest)
        res["ok"] = True
        res["type"] = cmd
        return res
    except Exception as e:
        return {"ok": False, "error": str(e), "type": cmd or "parse"}
