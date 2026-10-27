# -*- coding: utf-8 -*-
"""数学助教后端：Flask + SymPy（计算） + DeepSeek（讲解）。

运行：python app.py（或双击 start.bat）
手机在同一局域网通过 http://<电脑IP>:5000 访问。
"""
import json
import socket

from flask import Flask, Response, jsonify, request, send_from_directory

import solver
from explainer import stream_explain
from config import load_config

app = Flask(__name__, static_folder="static", static_url_path="/static")


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/sw.js")
def sw():
    # 服务到根路径，使 Service Worker 作用域为 /（否则只能控制 /static/，无法离线缓存首页）
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.post("/api/compute")
def api_compute():
    data = request.get_json(force=True, silent=True) or {}
    query = data.get("query", "")
    return jsonify(solver.compute(query))


@app.post("/api/explain")
def api_explain():
    data = request.get_json(force=True, silent=True) or {}
    query = data.get("query", "")
    computation = data.get("computation")
    cfg = load_config()
    if not cfg.get("deepseek_api_key"):
        return jsonify({"error": "尚未配置 DeepSeek API Key。请编辑 config.json，填入 deepseek_api_key。"}), 400

    def gen():
        try:
            for chunk in stream_explain(query, computation, cfg):
                yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    cfg = load_config()
    host = cfg.get("host", "0.0.0.0")
    port = int(cfg.get("port", 5000))
    ip = lan_ip()
    print("=" * 56)
    print("  数学助教已启动")
    print(f"  本机访问:   http://127.0.0.1:{port}")
    print(f"  手机访问:   http://{ip}:{port}   （需连接同一 WiFi）")
    print("  手机打不开时，请检查 Windows 防火墙是否放行此端口。")
    print("=" * 56)
    app.run(host=host, port=port, debug=False, threaded=True)
