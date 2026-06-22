# -*- coding: utf-8 -*-
"""
PetPlanta Web - app Flask que mostra o bichinho-planta animado e os dados
dos sensores em tempo real, lendo a porta serial do Arduino (ou simulando
dados se nenhum Arduino for encontrado).

Rodar:
    python app.py

Depois abra http://localhost:5000 no navegador.
"""

from flask import Flask, jsonify, render_template, request

import config
from serial_reader import start_background_reader

app = Flask(__name__)
state = start_background_reader()


@app.route("/")
def index():
    return render_template(
        "index.html",
        moods=config.MOODS,
        mood_labels=config.MOOD_LABELS,
        mood_bg=config.MOOD_BG,
        transition_ms=config.TRANSITION_DURATION_MS,
        transition_frames=config.TRANSITION_FRAMES,
        frame_ms=config.TRANSITION_FRAME_MS,
    )


@app.route("/api/state")
def api_state():
    return jsonify(state.to_dict())


@app.route("/api/config", methods=["GET"])
def api_config_get():
    return jsonify(config.get_editable_config())


@app.route("/api/config", methods=["POST"])
def api_config_post():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Corpo da requisicao invalido (esperado JSON)."}), 400
    try:
        novo = config.update_editable_config(body)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(novo)


@app.route("/api/simulation", methods=["GET"])
def api_simulation_get():
    return jsonify({"sim_mode": state.sim_mode, "sim_manual": dict(state.sim_manual)})


@app.route("/api/simulation", methods=["POST"])
def api_simulation_post():
    """Troca o modo de simulacao ("random"/"manual") e/ou os valores usados
    pelo modo manual. So tem efeito pratico enquanto o app estiver rodando
    sem Arduino conectado (state.simulated == True), mas aceita a chamada de
    qualquer forma - se um Arduino estiver conectado, os valores ficam
    guardados sem uso ate cair em simulacao."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Corpo da requisicao invalido (esperado JSON)."}), 400

    mode = body.get("sim_mode")
    if mode not in ("random", "manual"):
        return jsonify({"error": "'sim_mode' precisa ser 'random' ou 'manual'."}), 400

    manual_values = {}
    bounds = {
        "luz": ("Luz", 0, 1023),
        "solo": ("Solo", 0, 1023),
        "temperatura": ("Temperatura", -40, 100),
    }
    for key, (label, lo, hi) in bounds.items():
        if key in body and body[key] not in (None, ""):
            try:
                v = float(body[key])
            except (TypeError, ValueError):
                return jsonify({"error": f"Valor invalido em '{label}': precisa ser um numero"}), 400
            if not (lo <= v <= hi):
                return jsonify({"error": f"'{label}' precisa estar entre {lo} e {hi}"}), 400
            manual_values[key] = v

    state.set_sim_mode(mode)
    if manual_values:
        state.set_sim_manual_values(**manual_values)

    return jsonify({"sim_mode": state.sim_mode, "sim_manual": dict(state.sim_manual)})


if __name__ == "__main__":
    print(f"[PetPlanta] Servidor em http://localhost:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=False)
