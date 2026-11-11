/* Progress, quiz grading, and small UI updates.
   Correct answers are SHA-256(salt + "|" + choiceId). Explanations are base64. */
(function (root) {
  "use strict";

  var KEY = "coa-academy-progress-v1";
  var SIG_PREFIX = "care-ops-agent-academy|";

  function rightRotate(value, amount) {
    return (value >>> amount) | (value << (32 - amount));
  }

  function sha256(message) {
    var bytes = new TextEncoder().encode(message);
    var bitLen = bytes.length * 8;
    var withPad = bytes.length + 1;
    var zeros = (56 - (withPad % 64) + 64) % 64;
    var total = withPad + zeros + 8;
    var data = new Uint8Array(total);
    data.set(bytes);
    data[bytes.length] = 0x80;
    var view = new DataView(data.buffer);
    var hi = Math.floor(bitLen / 0x100000000);
    var lo = bitLen >>> 0;
    view.setUint32(total - 8, hi);
    view.setUint32(total - 4, lo);

    var k = [
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ];
    var h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];

    var w = new Array(64);
    for (var offset = 0; offset < data.length; offset += 64) {
      for (var i = 0; i < 16; i++) w[i] = view.getUint32(offset + i * 4);
      for (var j = 16; j < 64; j++) {
        var s0 = rightRotate(w[j - 15], 7) ^ rightRotate(w[j - 15], 18) ^ (w[j - 15] >>> 3);
        var s1 = rightRotate(w[j - 2], 17) ^ rightRotate(w[j - 2], 19) ^ (w[j - 2] >>> 10);
        w[j] = (w[j - 16] + s0 + w[j - 7] + s1) | 0;
      }
      var a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
      for (var t = 0; t < 64; t++) {
        var S1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
        var ch = (e & f) ^ (~e & g);
        var temp1 = (hh + S1 + ch + k[t] + w[t]) | 0;
        var S0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var temp2 = (S0 + maj) | 0;
        hh = g; g = f; f = e; e = (d + temp1) | 0; d = c; c = b; b = a; a = (temp1 + temp2) | 0;
      }
      h[0] = (h[0] + a) | 0; h[1] = (h[1] + b) | 0; h[2] = (h[2] + c) | 0; h[3] = (h[3] + d) | 0;
      h[4] = (h[4] + e) | 0; h[5] = (h[5] + f) | 0; h[6] = (h[6] + g) | 0; h[7] = (h[7] + hh) | 0;
    }
    var hex = "";
    for (var p = 0; p < 8; p++) hex += ("00000000" + (h[p] >>> 0).toString(16)).slice(-8);
    return hex;
  }

  function passMark() {
    return (root.SITE_CONFIG && root.SITE_CONFIG.passMark) || 0.8;
  }

  function emptyState() {
    return { version: 1, sessions: {} };
  }

  function load() {
    try {
      var raw = root.localStorage && root.localStorage.getItem(KEY);
      if (!raw) return emptyState();
      var data = JSON.parse(raw);
      if (!data || data.version !== 1 || !data.sessions) return emptyState();
      return data;
    } catch (err) {
      return emptyState();
    }
  }

  function save(state) {
    root.localStorage.setItem(KEY, JSON.stringify(state));
  }

  function sessionRecord(state, n) {
    return state.sessions[String(n)] || null;
  }

  function isPassed(state, n) {
    var rec = sessionRecord(state, n);
    return !!(rec && rec.passed);
  }

  function isUnlocked(state, n) {
    return n <= 1 || isPassed(state, n - 1);
  }

  function bytesToB64Url(bytes) {
    var bin = "";
    for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  function b64UrlToString(b64) {
    var pad = b64.replace(/-/g, "+").replace(/_/g, "/");
    while (pad.length % 4) pad += "=";
    var bin = atob(pad);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder().decode(bytes);
  }

  function exportState(state) {
    var json = JSON.stringify(state);
    var payload = bytesToB64Url(new TextEncoder().encode(json));
    var sig = sha256(SIG_PREFIX + payload).slice(0, 12);
    return "COA1." + payload + "." + sig;
  }

  function importState(code) {
    var text = String(code || "").trim().replace(/\s+/g, "");
    var parts = text.split(".");
    if (parts.length !== 3 || parts[0] !== "COA1") throw new Error("That code does not start with COA1.");
    var sig = sha256(SIG_PREFIX + parts[1]).slice(0, 12);
    if (sig !== parts[2]) throw new Error("The checksum does not match. Copy the whole code.");
    var data = JSON.parse(b64UrlToString(parts[1]));
    if (!data || data.version !== 1 || !data.sessions) throw new Error("The progress payload is not a version 1 record.");
    return data;
  }

  function choiceMatches(question, choiceId) {
    return sha256(question.salt + "|" + choiceId) === question.answerHash;
  }

  function decodeExplain(b64) {
    return b64UrlToString(b64);
  }

  function recordScore(state, session, score, passed) {
    var id = String(session);
    var prev = state.sessions[id] || { best: 0, passed: false, attempts: 0 };
    var best = Math.max(prev.best || 0, score);
    state.sessions[id] = {
      best: best,
      passed: !!(prev.passed || passed),
      attempts: (prev.attempts || 0) + 1,
      updated: new Date().toISOString(),
    };
    return state.sessions[id];
  }

  function passedCount(state) {
    var n = 0;
    for (var i = 1; i <= 10; i++) if (isPassed(state, i)) n += 1;
    return n;
  }

  function paintNav(state, active) {
    var links = document.querySelectorAll(".nav a.item[data-session]");
    links.forEach(function (link) {
      var n = Number(link.getAttribute("data-session"));
      if (!n) return;
      var open = isUnlocked(state, n);
      link.classList.toggle("locked", !open);
      link.classList.toggle("active", n === active);
      var dot = link.querySelector(".dot");
      if (!dot) return;
      dot.classList.toggle("pass", isPassed(state, n));
      dot.classList.toggle("now", open && !isPassed(state, n));
    });
    var foot = document.getElementById("nav-progress");
    if (foot) foot.textContent = passedCount(state) + " of 10 quizzes passed";
  }

  function paintHome(state) {
    var done = passedCount(state);
    var pct = (done / 10) * 100;
    document.querySelectorAll("[data-progress]").forEach(function (el) {
      el.style.setProperty("--p", String(pct));
    });
    var label = document.getElementById("progress-label");
    if (label) label.textContent = done + " of 10 sessions passed";
    var ringLabel = document.getElementById("ring-label");
    if (ringLabel) ringLabel.textContent = done + "/10";
    var detail = document.getElementById("progress-detail");
    if (detail) {
      detail.textContent = done === 10
        ? "You have passed every quiz. The scaling workbook is the last artifact."
        : "Pass a quiz at 80% or better, 5 of 6, to open the next session. Retries are unlimited.";
    }
    document.querySelectorAll(".session-card").forEach(function (card) {
      var n = Number(card.getAttribute("data-session"));
      var pill = card.querySelector(".pill");
      var open = isUnlocked(state, n);
      card.setAttribute("href", open ? "session-" + n + ".html" : "#");
      card.setAttribute("aria-disabled", open ? "false" : "true");
      if (!open) {
        pill.textContent = "Locked";
        pill.className = "pill lock";
      } else if (isPassed(state, n)) {
        var rec = sessionRecord(state, n);
        pill.textContent = "Passed " + Math.round(rec.best * 100) + "%";
        pill.className = "pill pass";
      } else {
        pill.textContent = "Open";
        pill.className = "pill";
      }
    });
  }

  function paintLinks() {
    var cfg = root.SITE_CONFIG || {};
    var gh = document.getElementById("link-github");
    if (gh && cfg.githubRepo) gh.href = cfg.githubRepo;
    var jira = document.getElementById("link-jira");
    if (jira && cfg.jiraProjects) {
      jira.href = cfg.jiraProjects;
      var sub = jira.querySelector("p");
      if (sub) sub.textContent = "Project key " + cfg.jiraProjectKey + ". Import docs/jira/backlog.json on this free site. The browse link is " + cfg.jiraBrowse + ".";
    }
    var st = document.getElementById("link-streamlit");
    if (st) {
      var url = (cfg.streamlitUrl || "").trim();
      var p = st.querySelector("p");
      if (url) {
        st.href = url;
        st.classList.remove("warn");
        if (p) p.textContent = url;
      } else {
        st.removeAttribute("href");
        st.classList.add("warn");
        if (p) p.textContent = "Needs a URL. Set streamlitUrl in js/site-config.js. It was not in the repo.";
      }
    }
  }

  function wireTransfer() {
    var out = document.getElementById("export-code");
    var exp = document.getElementById("export-btn");
    var imp = document.getElementById("import-btn");
    var inp = document.getElementById("import-code");
    var msg = document.getElementById("transfer-msg");
    if (exp && out) {
      exp.addEventListener("click", function () {
        var code = exportState(load());
        out.value = code;
        out.focus();
        out.select();
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(code).then(function () {
            if (msg) msg.textContent = "Copied. Paste this on your other computer, then Import.";
          }, function () {
            if (msg) msg.textContent = "Select the code and copy it. Clipboard permission was blocked.";
          });
        }
      });
    }
    if (imp && inp) {
      imp.addEventListener("click", function () {
        try {
          var data = importState(inp.value);
          save(data);
          if (msg) msg.textContent = "Imported " + passedCount(data) + " passed session" + (passedCount(data) === 1 ? "" : "s") + ".";
          boot();
        } catch (err) {
          if (msg) msg.textContent = err.message || "Could not import that code.";
        }
      });
    }
    var reset = document.getElementById("reset-btn");
    if (reset) {
      reset.addEventListener("click", function () {
        if (!root.confirm("Clear quiz progress in this browser?")) return;
        save(emptyState());
        if (msg) msg.textContent = "Progress cleared on this browser.";
        boot();
      });
    }
  }

  function mountQuiz(session) {
    var host = document.getElementById("quiz");
    if (!host || !root.QUIZZES) return;
    var pack = root.QUIZZES[String(session)];
    if (!pack) {
      host.textContent = "Quiz data is missing for this session.";
      return;
    }
    var mark = pack.passMark || passMark();
    host.innerHTML = "";
    pack.questions.forEach(function (q, index) {
      var fs = document.createElement("fieldset");
      fs.className = "q";
      fs.id = "q-" + q.id;
      var legend = document.createElement("legend");
      legend.textContent = (index + 1) + ". " + q.prompt;
      fs.appendChild(legend);
      q.choices.forEach(function (choice) {
        var label = document.createElement("label");
        label.className = "choice";
        var input = document.createElement("input");
        input.type = "radio";
        input.name = q.id;
        input.value = choice.id;
        label.appendChild(input);
        var span = document.createElement("span");
        span.textContent = choice.text;
        label.appendChild(span);
        fs.appendChild(label);
      });
      var explain = document.createElement("p");
      explain.className = "explain";
      explain.hidden = true;
      fs.appendChild(explain);
      host.appendChild(fs);
    });
    var actions = document.createElement("div");
    actions.className = "quiz-actions";
    var submit = document.createElement("button");
    submit.type = "button";
    submit.textContent = "Check answers";
    var again = document.createElement("button");
    again.type = "button";
    again.className = "secondary";
    again.textContent = "Try again";
    again.hidden = true;
    actions.appendChild(submit);
    actions.appendChild(again);
    host.appendChild(actions);
    var result = document.createElement("div");
    result.className = "result";
    result.setAttribute("role", "status");
    host.appendChild(result);
    var next = document.createElement("p");
    host.appendChild(next);

    function grade() {
      var correct = 0;
      var missed = false;
      pack.questions.forEach(function (q) {
        var picked = host.querySelector("input[name='" + q.id + "']:checked");
        var fs = document.getElementById("q-" + q.id);
        var explain = fs.querySelector(".explain");
        var right = null;
        q.choices.forEach(function (choice) {
          if (choiceMatches(q, choice.id)) right = choice.id;
        });
        var ok = picked && picked.value === right;
        if (ok) correct += 1;
        else missed = true;
        fs.classList.toggle("good", !!ok);
        fs.classList.toggle("bad", !ok);
        explain.hidden = false;
        explain.textContent = decodeExplain(q.explain);
        fs.querySelectorAll("input").forEach(function (input) { input.disabled = true; });
      });
      var score = correct / pack.questions.length;
      var passed = score + 1e-9 >= mark;
      var state = load();
      var rec = recordScore(state, session, score, passed);
      save(state);
      var pct = Math.round(score * 100);
      result.textContent = correct + " of " + pack.questions.length + " · " + pct + "% · " + (passed || rec.passed ? "passed" : "need 80%");
      again.hidden = false;
      submit.disabled = true;
      if (rec.passed && session < 10) {
        next.innerHTML = "Session " + (session + 1) + " is unlocked. <a class='button' href='session-" + (session + 1) + ".html'>Continue</a>";
      } else if (rec.passed) {
        next.textContent = "That was the last session. The home page is your scorecard.";
      } else {
        next.textContent = "Nothing is used up. Change your mind and try again. The best score is the one that counts.";
      }
      paintNav(load(), session);
      if (missed) result.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    submit.addEventListener("click", grade);
    again.addEventListener("click", function () { mountQuiz(session); });

    var prior = sessionRecord(load(), session);
    if (prior && prior.attempts) {
      var priorNote = document.createElement("p");
      priorNote.className = "note";
      priorNote.textContent = "Best so far: " + Math.round(prior.best * 100) + "% over " + prior.attempts + " attempt" + (prior.attempts === 1 ? "" : "s") + (prior.passed ? ". This session is already passed." : ".");
      host.insertBefore(priorNote, host.firstChild);
    }
  }

  function boot() {
    var state = load();
    var body = document.body;
    var page = body.getAttribute("data-page");
    var session = Number(body.getAttribute("data-session") || "0");
    paintNav(state, session);
    paintLinks();
    if (page === "home") {
      paintHome(state);
      if (!document.body.getAttribute("data-wired")) {
        document.body.setAttribute("data-wired", "1");
        wireTransfer();
        document.querySelectorAll(".session-card").forEach(function (card) {
          card.addEventListener("click", function (event) {
            var n = Number(card.getAttribute("data-session"));
            if (!isUnlocked(load(), n)) {
              event.preventDefault();
              var note = document.getElementById("lock-note");
              if (note) note.textContent = "Session " + n + " stays locked until you pass Session " + (n - 1) + " at 80% or better.";
            }
          });
        });
      }
    }
    if (page === "session") mountQuiz(session);
  }

  var api = {
    sha256: sha256,
    exportState: exportState,
    importState: importState,
    choiceMatches: choiceMatches,
    emptyState: emptyState,
    KEY: KEY,
  };
  root.IAAcademy = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
    else boot();
  }
})(typeof window !== "undefined" ? window : globalThis);
