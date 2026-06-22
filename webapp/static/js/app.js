(function () {
  const img = document.getElementById("pet-gif");
  const moodLabel = document.getElementById("mood-label");
  const badgeConexao = document.getElementById("badge-conexao");
  const badgeSim = document.getElementById("badge-sim");
  const lastUpdateEl = document.getElementById("last-update");

  const valLuz = document.getElementById("val-luz");
  const valSolo = document.getElementById("val-solo");
  const valTemp = document.getElementById("val-temp");

  const barLuz = document.getElementById("bar-luz");
  const barSolo = document.getElementById("bar-solo");
  const barTemp = document.getElementById("bar-temp");

  const countdownLuz = document.getElementById("countdown-luz");
  const countdownSolo = document.getElementById("countdown-solo");
  const ultimaRegaEl = document.getElementById("ultima-rega");

  const btnSim = document.getElementById("btn-sim");

  // Escalas usadas so para desenhar a barra de progresso de cada sensor
  // (nao tem relacao com os thresholds de mood em config.py).
  const BAR_MAX = { luz: 1023, solo: 600, temp: 40 };

  // Cores fixas usadas nas barras (verde/amarelo/vermelho do projeto).
  const BAR_COLOR_GREEN = "#4fa861";
  const BAR_COLOR_YELLOW = "#e0a23b";
  const BAR_COLOR_RED = "#d9534f";
  // Azul clarinho da barra de temperatura quando "com frio" - usa a MESMA
  // cor configurada em config.MOOD_BG["frio"] (exposta via window.MOOD_BG),
  // entao se a paleta mudar la, a barra acompanha sem precisar editar JS.
  const BAR_COLOR_FRIO = (window.MOOD_BG && window.MOOD_BG.frio) || "rgb(213, 238, 250)";
  // Limiar amarelo/verde da barra de solo - independente da escala visual
  // (BAR_MAX.solo), pra mudar o tamanho da barra sem mudar quando ela fica
  // amarela ou verde.
  const SOLO_AMARELO_MAX = 300;

  function numOr(value, fallback) {
    return value === null || value === undefined ? fallback : value;
  }

  // Cor da barra de luz: vermelho se estiver no limiar de "dormindo" (sem
  // luz), senao amarelo até 40% da escala da barra, verde dali pra cima.
  function colorForLuz(value, data) {
    if (value === null || value === undefined) return BAR_COLOR_GREEN;
    const luzEscuroMax = numOr(data.luz_escuro_max, 400);
    if (value <= luzEscuroMax) return BAR_COLOR_RED;
    const pct = value / BAR_MAX.luz;
    return pct <= 0.4 ? BAR_COLOR_YELLOW : BAR_COLOR_GREEN;
  }

  // Cor da barra de solo: vermelho se estiver no limiar de "seca", amarelo
  // se estiver até SOLO_AMARELO_MAX, verde acima disso.
  function colorForSolo(value, data) {
    if (value === null || value === undefined) return BAR_COLOR_GREEN;
    const soloSecoMax = numOr(data.solo_seco_max, 250);
    if (value < soloSecoMax) return BAR_COLOR_RED;
    return value <= SOLO_AMARELO_MAX ? BAR_COLOR_YELLOW : BAR_COLOR_GREEN;
  }

  // Cor da barra de temperatura: azul claro (frio), vermelho (calor extremo
  // / doente), verde no meio.
  function colorForTemp(value, data) {
    if (value === null || value === undefined) return BAR_COLOR_GREEN;
    const tempFrioMax = numOr(data.temp_frio_max, 15);
    const tempDoenteMin = numOr(data.temp_doente_min, 40);
    if (value <= tempFrioMax) return BAR_COLOR_FRIO;
    if (value >= tempDoenteMin) return BAR_COLOR_RED;
    return BAR_COLOR_GREEN;
  }

  let currentMood = null;
  let transitioning = false;
  let rafId = null;

  function loopUrl(mood) {
    return `/static/gifs/loop_${mood}.gif`;
  }

  function transitionFrameUrl(fromMood, toMood, frameIdx) {
    return `/static/gifs/transition_${fromMood}_to_${toMood}/frame_${frameIdx}.png`;
  }

  // Pre-carrega os loops e TODOS os frames PNG de transicao na memoria do
  // navegador assim que a pagina abre, pra quando o mood mudar de verdade
  // tudo ja estar em cache e a troca ser instantanea (sem espera de rede).
  function preloadAssets() {
    const moods = (window.MOOD_LABELS && Object.keys(window.MOOD_LABELS)) || [];
    const steps = window.TRANSITION_FRAMES || 8;

    moods.forEach((m) => {
      new Image().src = loopUrl(m);
    });

    moods.forEach((a) => {
      moods.forEach((b) => {
        if (a === b) return;
        for (let i = 1; i <= steps; i++) {
          new Image().src = transitionFrameUrl(a, b, i);
        }
      });
    });
  }

  // Toca a transicao "na mao": em vez de soltar um GIF animado e deixar o
  // navegador decidir quando trocar de frame (timing de GIF nativo NAO e
  // confiavel/sincronizavel com JS - cada engine arredonda/decodifica os
  // delays do seu jeito, sem garantia de ficar em fase com o relogio da
  // pagina), o app troca a imagem do bichinho (frames PNG estaticos) num
  // loop de requestAnimationFrame baseado no tempo decorrido desde o
  // inicio da transicao. O fundo da pagina fica fixo (branco) - so a
  // imagem do bichinho muda.
  function playTransition(fromMood, toMood) {
    const steps = window.TRANSITION_FRAMES || 8;
    const frameMs = window.FRAME_MS || 90;
    const totalMs = steps * frameMs;

    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }

    const startTime = performance.now();
    let lastFrameIdx = 0;

    const tick = () => {
      const elapsed = performance.now() - startTime;
      const frameIdx = Math.min(steps, Math.floor(elapsed / frameMs) + 1);

      if (frameIdx !== lastFrameIdx) {
        lastFrameIdx = frameIdx;
        img.src = transitionFrameUrl(fromMood, toMood, frameIdx);
      }

      if (elapsed < totalMs) {
        rafId = requestAnimationFrame(tick);
      } else {
        rafId = null;
        img.src = loopUrl(toMood);
        currentMood = toMood;
        transitioning = false;
      }
    };

    tick();
  }

  function applyMood(newMood, animate) {
    const label = (window.MOOD_LABELS && window.MOOD_LABELS[newMood]) || newMood;
    moodLabel.textContent = label;

    if (!animate || currentMood === null) {
      img.src = loopUrl(newMood);
      currentMood = newMood;
      return;
    }

    if (newMood === currentMood || transitioning) {
      return;
    }

    transitioning = true;
    playTransition(currentMood, newMood);
  }

  function fmt(value, suffix, digits) {
    if (value === null || value === undefined) return "--";
    if (typeof digits === "number") return value.toFixed(digits) + suffix;
    return value + suffix;
  }

  function setBar(el, value, max) {
    if (value === null || value === undefined) {
      el.style.width = "0%";
      return;
    }
    const pct = Math.max(0, Math.min(100, (value / max) * 100));
    el.style.width = pct + "%";
  }

  function setBarColor(el, color) {
    el.style.backgroundColor = color;
  }

  // Mostra "Critico em Xh Ym Zs" enquanto a condicao (seca/dormindo) estiver
  // ativa; quando o tempo zera, mostra que ja virou critico. Esconde o
  // contador quando a condicao nao esta mais ativa (valor null).
  function setCountdown(el, secondsRemaining) {
    if (secondsRemaining === null || secondsRemaining === undefined) {
      el.classList.add("hidden");
      el.classList.remove("critico");
      return;
    }

    el.classList.remove("hidden");

    if (secondsRemaining <= 0) {
      el.textContent = "Critico!";
      el.classList.add("critico");
      return;
    }

    el.classList.remove("critico");
    const total = Math.floor(secondsRemaining);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    el.textContent = `Critico em ${h}h ${m}m ${s}s`;
  }

  // Mostra "Ultima rega Xh Ym atras" desde a ultima vez que o solo cruzou
  // REGA_DETECTADA_MIN subindo (ver serial_reader.py). Fica visivel e so
  // cresce até a proxima rega ser detectada - nao some so porque o solo
  // secou de novo. secondsAgo null = nenhuma rega detectada ainda.
  function setUltimaRega(el, secondsAgo) {
    if (secondsAgo === null || secondsAgo === undefined) {
      el.classList.add("hidden");
      return;
    }

    el.classList.remove("hidden");
    const total = Math.floor(secondsAgo);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);

    if (h > 0) {
      el.textContent = `Última rega ${h}h ${m}m atrás`;
    } else if (m > 0) {
      el.textContent = `Última rega ${m}m atrás`;
    } else {
      el.textContent = "Última rega agora";
    }
  }

  async function poll() {
    try {
      const res = await fetch("/api/state", { cache: "no-store" });
      const data = await res.json();

      valLuz.textContent = fmt(data.luz, "");
      valSolo.textContent = fmt(data.solo, "");
      valTemp.textContent = fmt(data.temperatura, " °C", 1);

      setBar(barLuz, data.luz, BAR_MAX.luz);
      setBar(barSolo, data.solo, BAR_MAX.solo);
      setBar(barTemp, data.temperatura, BAR_MAX.temp);

      setBarColor(barLuz, colorForLuz(data.luz, data));
      setBarColor(barSolo, colorForSolo(data.solo, data));
      setBarColor(barTemp, colorForTemp(data.temperatura, data));

      setCountdown(countdownLuz, data.dormindo_restante_s);
      setCountdown(countdownSolo, data.seca_restante_s);
      setUltimaRega(ultimaRegaEl, data.ultima_rega_s_atras);

      if (data.connected) {
        badgeConexao.textContent = "conectado";
        badgeConexao.className = "badge online";
      } else {
        badgeConexao.textContent = "sem leituras recentes";
        badgeConexao.className = "badge offline";
      }
      badgeSim.classList.toggle("hidden", !data.simulated);
      if (btnSim) btnSim.classList.toggle("hidden", !data.simulated);
      syncSimPanelFromState(data);

      if (data.last_update) {
        const d = new Date(data.last_update * 1000);
        lastUpdateEl.textContent = d.toLocaleTimeString();
      }

      applyMood(data.mood, true);
    } catch (err) {
      badgeConexao.textContent = "erro de conexao";
      badgeConexao.className = "badge offline";
    }
  }

  // --- Tela de configuracoes (limiares editaveis) ---
  const btnConfig = document.getElementById("btn-config");
  const btnConfigClose = document.getElementById("btn-config-close");
  const btnConfigCancel = document.getElementById("btn-config-cancel");
  const overlay = document.getElementById("config-overlay");
  const configForm = document.getElementById("config-form");
  const configError = document.getElementById("config-error");
  const btnConfigSave = document.getElementById("btn-config-save");

  function showConfigError(msg) {
    configError.textContent = msg;
    configError.classList.remove("hidden");
  }

  function hideConfigError() {
    configError.classList.add("hidden");
  }

  function fillConfigForm(data) {
    Object.keys(data).forEach((key) => {
      const input = configForm.elements.namedItem(key);
      if (input) input.value = data[key];
    });
  }

  async function openConfigModal() {
    hideConfigError();
    overlay.classList.remove("hidden");
    try {
      const res = await fetch("/api/config", { cache: "no-store" });
      if (!res.ok) throw new Error("Nao foi possivel carregar as configuracoes atuais.");
      const data = await res.json();
      fillConfigForm(data);
    } catch (err) {
      showConfigError(err.message || "Erro ao carregar configuracoes.");
    }
  }

  function closeConfigModal() {
    overlay.classList.add("hidden");
    hideConfigError();
  }

  function readConfigForm() {
    const formData = new FormData(configForm);
    const values = {};
    formData.forEach((value, key) => {
      values[key] = value;
    });
    return values;
  }

  async function saveConfig(ev) {
    ev.preventDefault();
    hideConfigError();
    btnConfigSave.disabled = true;
    btnConfigSave.textContent = "Salvando...";
    try {
      const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(readConfigForm()),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Nao foi possivel salvar as configuracoes.");
      }
      fillConfigForm(data);
      closeConfigModal();
    } catch (err) {
      showConfigError(err.message || "Erro ao salvar configuracoes.");
    } finally {
      btnConfigSave.disabled = false;
      btnConfigSave.textContent = "Salvar";
    }
  }

  if (btnConfig) btnConfig.addEventListener("click", openConfigModal);
  if (btnConfigClose) btnConfigClose.addEventListener("click", closeConfigModal);
  if (btnConfigCancel) btnConfigCancel.addEventListener("click", closeConfigModal);
  if (overlay) {
    overlay.addEventListener("click", (ev) => {
      if (ev.target === overlay) closeConfigModal();
    });
  }
  if (configForm) configForm.addEventListener("submit", saveConfig);
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !overlay.classList.contains("hidden")) closeConfigModal();
  });

  // --- Tela de simulacao (modo aleatorio/manual + valores de luz/solo/temp) ---
  const btnSimClose = document.getElementById("btn-sim-close");
  const btnSimCancel = document.getElementById("btn-sim-cancel");
  const simOverlay = document.getElementById("sim-overlay");
  const simForm = document.getElementById("sim-form");
  const simError = document.getElementById("sim-error");
  const btnSimSave = document.getElementById("btn-sim-save");
  const simModeRandom = document.getElementById("sim-mode-random");
  const simModeManual = document.getElementById("sim-mode-manual");
  const simLuz = document.getElementById("sim-luz");
  const simSolo = document.getElementById("sim-solo");
  const simTemp = document.getElementById("sim-temp");

  // So preenche os campos com o que vem do /api/state na PRIMEIRA vez que o
  // painel aparece (ou depois de fechado/reaberto) - assim nao fica
  // sobrescrevendo o que o usuario esta digitando a cada poll de 2s.
  let simSyncedOnce = false;

  function updateSimFieldsDisabled() {
    const manual = simModeManual.checked;
    simLuz.disabled = !manual;
    simSolo.disabled = !manual;
    simTemp.disabled = !manual;
  }

  function syncSimPanelFromState(data) {
    if (!data.simulated) {
      simSyncedOnce = false;
      return;
    }
    if (simSyncedOnce) return;
    simSyncedOnce = true;
    (data.sim_mode === "manual" ? simModeManual : simModeRandom).checked = true;
    if (data.sim_manual) {
      simLuz.value = data.sim_manual.luz;
      simSolo.value = data.sim_manual.solo;
      simTemp.value = data.sim_manual.temperatura;
    }
    updateSimFieldsDisabled();
  }

  function showSimError(msg) {
    simError.textContent = msg;
    simError.classList.remove("hidden");
  }

  function hideSimError() {
    simError.classList.add("hidden");
  }

  function openSimModal() {
    hideSimError();
    simOverlay.classList.remove("hidden");
  }

  function closeSimModal() {
    simOverlay.classList.add("hidden");
    hideSimError();
  }

  async function saveSim(ev) {
    ev.preventDefault();
    hideSimError();
    btnSimSave.disabled = true;
    btnSimSave.textContent = "Aplicando...";
    try {
      const body = { sim_mode: simModeManual.checked ? "manual" : "random" };
      if (body.sim_mode === "manual") {
        body.luz = simLuz.value;
        body.solo = simSolo.value;
        body.temperatura = simTemp.value;
      }
      const res = await fetch("/api/simulation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Nao foi possivel aplicar a simulacao.");
      }
      closeSimModal();
    } catch (err) {
      showSimError(err.message || "Erro ao aplicar simulacao.");
    } finally {
      btnSimSave.disabled = false;
      btnSimSave.textContent = "Aplicar";
    }
  }

  if (btnSim) btnSim.addEventListener("click", openSimModal);
  if (btnSimClose) btnSimClose.addEventListener("click", closeSimModal);
  if (btnSimCancel) btnSimCancel.addEventListener("click", closeSimModal);
  if (simOverlay) {
    simOverlay.addEventListener("click", (ev) => {
      if (ev.target === simOverlay) closeSimModal();
    });
  }
  if (simForm) simForm.addEventListener("submit", saveSim);
  if (simModeRandom) simModeRandom.addEventListener("change", updateSimFieldsDisabled);
  if (simModeManual) simModeManual.addEventListener("change", updateSimFieldsDisabled);
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !simOverlay.classList.contains("hidden")) closeSimModal();
  });

  preloadAssets();
  poll();
  setInterval(poll, 2000);
})();
