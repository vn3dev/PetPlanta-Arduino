# -*- coding: utf-8 -*-
"""
Logica que traduz as leituras dos sensores em um "humor" (mood) AMBIENTAL do
bichinho - SEM considerar "festa" nem "critico", que dependem de estado e
tempo acumulado (nao so da leitura atual) e por isso sao orquestrados em
serial_reader.py (SharedState._recompute_mood_locked), que decide a
prioridade final: festa > critico > o que esta funcao devolver.

Prioridade dos estados (do mais forte para o mais fraco):
1. dormindo  -> sem luz (de noite a planta dorme, independente do resto)
2. frio      -> temperatura muito baixa
3. doente    -> temperatura muito alta por calor extremo
4. seca      -> solo seco
5. oculos    -> bastante luz / sol forte, sem nenhum problema acima
6. feliz     -> nenhuma condicao especial, tudo dentro da faixa ideal
"""

import config


def compute_mood(luz, solo, temperatura):
    """Recebe as 3 leituras do Arduino e devolve o mood ambiental atual.

    Qualquer leitura pode vir None (sensor falhou / ainda nao chegou nenhuma
    leitura) - nesse caso a condicao correspondente simplesmente nao dispara.
    """

    if luz is not None and luz <= config.LUZ_ESCURO_MAX:
        return "dormindo"

    if temperatura is not None and temperatura <= config.TEMP_FRIO_MAX:
        return "frio"

    if temperatura is not None and temperatura >= config.TEMP_DOENTE_MIN:
        return "doente"

    if solo is not None and solo < config.SOLO_SECO_MAX:
        return "seca"

    if luz is not None and luz >= config.LUZ_ENSOLARADO_MIN:
        return "oculos"

    return "feliz"
