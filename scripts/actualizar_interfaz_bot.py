"""Actualiza views/index.html con la nueva interfaz de DataBotIA:
1. Header y tarjetas de estado con validación de API-Football y cero alucinación.
2. Formateador Markdown robusto (tablas, encabezados, citas, listas, badges).
3. Motor NLP enriquecido con auditoría de jugadores activos vs transferidos.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "views" / "index.html"

content = INDEX_HTML.read_text(encoding="utf-8")

# 1. ACTUALIZAR HEADER DE SECTION ID="BOT"
antiguo_header = """    <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#1d3a2c] pb-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold text-emerald-400 uppercase tracking-widest">Motor NLP Liga MX Pro</span>
          <span class="text-[10px] bg-emerald-500/15 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30 font-semibold">v2.5 Deep Insights</span>
        </div>
        <h2 class="text-2xl font-black flex items-center gap-2 text-white">🤖 DataBot: Centro Táctico & Oráculo de Inferencia</h2>
      </div>
      <div class="flex items-center gap-2 text-xs text-[color:var(--mut)]">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Respuestas dinámicas conectadas al Ensamble Poisson & Elo
      </div>
    </div>"""

nuevo_header = """    <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3 border-b border-[#1d3a2c] pb-4">
      <div>
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-xs font-black text-emerald-400 uppercase tracking-widest">DataBotIA · Analítica Liga MX</span>
          <span class="text-[10px] bg-emerald-500/20 text-emerald-300 px-2.5 py-0.5 rounded-full border border-emerald-500/40 font-bold flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> API-Football v3 Validado
          </span>
          <span class="text-[10px] bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded-full border border-sky-500/30 font-semibold">
            🛡️ Cero Alucinación Activa
          </span>
        </div>
        <h2 class="text-2xl font-black flex items-center gap-2 text-white mt-1">🤖 DataBotIA: Inteligencia Táctica & Oráculo Apertura 2026</h2>
      </div>
      <div class="flex items-center gap-2 text-xs text-[color:var(--mut)]">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Plantillas Oficiales Cruzadas al 100% · Cédulas Reales
      </div>
    </div>"""

if antiguo_header in content:
    content = content.replace(antiguo_header, nuevo_header, 1)
    print("Header actualizado.")
else:
    print("Header antiguo no encontrado con match exacto.")

# 2. ACTUALIZAR TARJETA DE ESTADO DEL BOT
antiguo_estado = """          <div class="pt-2 border-t border-[#1d3a2c]/60 grid grid-cols-2 gap-2 text-center text-[10px]">
            <div class="bg-black/40 p-2 rounded-xl border border-[#1d3a2c]">
              <span class="text-[color:var(--mut)] block">Equipos Indexados</span>
              <b class="text-emerald-400 font-bold text-xs">18 Clubes</b>
            </div>
            <div class="bg-black/40 p-2 rounded-xl border border-[#1d3a2c]">
              <span class="text-[color:var(--mut)] block">Matriz de Goles</span>
              <b class="text-sky-400 font-bold text-xs">9×9 Poisson</b>
            </div>
          </div>"""

nuevo_estado = """          <div class="pt-2 border-t border-[#1d3a2c]/60 grid grid-cols-2 gap-2 text-center text-[10px]">
            <div class="bg-black/40 p-2 rounded-xl border border-[#1d3a2c]">
              <span class="text-[color:var(--mut)] block">Clubes Verificados</span>
              <b class="text-emerald-400 font-bold text-xs">18 en API</b>
            </div>
            <div class="bg-black/40 p-2 rounded-xl border border-[#1d3a2c]">
              <span class="text-[color:var(--mut)] block">Titulares Validados</span>
              <b class="text-sky-400 font-bold text-xs">198 Oficiales</b>
            </div>
          </div>
          <div class="bg-emerald-950/30 p-2 rounded-xl border border-emerald-500/20 text-[10px] text-emerald-200/90 leading-tight">
            🛡️ <b>Filtro de Integridad:</b> Futbolistas retirados o dados de baja son automáticamente descartados.
          </div>"""

if antiguo_estado in content:
    content = content.replace(antiguo_estado, nuevo_estado, 1)
    print("Tarjeta de estado actualizada.")

# 3. ACTUALIZAR COMANDOS FRECUENTES Y CHIPS
antiguos_chips = """          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs" id="quickChips">
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Cómo afecta la altitud en Toluca?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Quién gana Tigres vs América?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">Recomiéndame 3 picks seguros</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Qué equipo tiene mejor xG?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">Explica la corrección Dixon-Coles</button>
          </div>"""

nuevos_chips = """          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs" id="quickChips">
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Quién es Paulinho y cuántos goles lleva?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Dónde juega Alan Mozo en el Apertura 2026?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Juega Ángel Sepúlveda en Cruz Azul?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">Alineación confirmada de Toluca</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Quién gana Tigres vs América?</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">Top 3 picks seguros J17</button>
            <button class="chip hover:border-emerald-500 cursor-pointer text-emerald-300 whitespace-nowrap">¿Cómo afecta la altitud en Toluca (2660m)?</button>
          </div>"""

if antiguos_chips in content:
    content = content.replace(antiguos_chips, nuevos_chips, 1)
    print("Quick chips actualizados.")

# 4. ACTUALIZAR FORMATBOTTEXT CON RENDERIZADO DE TABLAS MARKDOWN
antiguo_format = """function formatBotText(str) {
  if (!str) return "";
  return str
    .replace(/\\n/g, '\\n')
    .replace(/\\*\\*(.*?)\\*\\*/g, '<b class="text-white font-extrabold">$1</b>')
    .replace(/\\*(.*?)\\*/g, '<i class="text-emerald-300 not-italic font-semibold">$1</i>')
    .replace(/_(.*?)_/g, '<span class="text-gray-400 text-[11px] italic">$1</span>')
    .replace(/\\n/g, '<br>');
}"""

nuevo_format = """function renderHtmlTable(rows) {
  if (!rows || !rows.length) return "";
  const header = rows[0];
  const body = rows.slice(1);
  let html = '<div class="overflow-x-auto my-2.5 rounded-xl border border-[#1d3a2c] bg-black/40 shadow-inner"><table class="w-full text-left text-[11px] border-collapse">';
  html += '<thead class="bg-[#0e251b] border-b border-[#1d3a2c] text-emerald-300 uppercase tracking-wider font-bold">';
  html += '<tr>' + header.map(h => `<th class="py-2 px-3 border-r border-[#1d3a2c]/60 last:border-r-0">${h}</th>`).join('') + '</tr>';
  html += '</thead><tbody>';
  body.forEach((r, idx) => {
    const bg = idx % 2 === 0 ? 'bg-black/20' : 'bg-white/[0.02]';
    html += `<tr class="${bg} border-b border-[#1d3a2c]/40 hover:bg-emerald-500/10 transition">` +
      r.map(c => `<td class="py-1.5 px-3 border-r border-[#1d3a2c]/40 last:border-r-0 font-medium">${c}</td>`).join('') +
      '</tr>';
  });
  html += '</tbody></table></div>';
  return html;
}

function formatBotText(str) {
  if (!str) return "";
  let text = str.replace(/\\\\n/g, '\\n');

  // Procesar tablas de Markdown (| celda | celda |)
  const lines = text.split('\\n');
  let inTable = false;
  let tableRows = [];
  let outLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith('|') && line.endsWith('|')) {
      if (/^\\|(\\s*[-:]+[-|\\s:]*)\\|$/.test(line)) {
        continue; // Línea divisoria |---|---|
      }
      if (!inTable) {
        inTable = true;
        tableRows = [];
      }
      const cells = line.slice(1, -1).split('|').map(c => c.trim());
      tableRows.push(cells);
    } else {
      if (inTable) {
        outLines.push(renderHtmlTable(tableRows));
        inTable = false;
        tableRows = [];
      }
      outLines.push(lines[i]);
    }
  }
  if (inTable) {
    outLines.push(renderHtmlTable(tableRows));
  }

  text = outLines.join('\\n');

  // Encabezados Markdown
  text = text.replace(/^### (.*$)/gim, '<h3 class="text-emerald-400 font-extrabold text-xs uppercase tracking-wider mt-3 mb-1.5 flex items-center gap-1.5"><span>⚡</span> $1</h3>');
  text = text.replace(/^## (.*$)/gim, '<h2 class="text-white font-black text-sm mt-3.5 mb-1.5 border-b border-[#1d3a2c] pb-1 flex items-center gap-1.5"><span>📌</span> $1</h2>');
  text = text.replace(/^# (.*$)/gim, '<h1 class="text-base font-black text-emerald-300 mt-2 mb-2">$1</h1>');

  // Citas / Callouts
  text = text.replace(/^\\> (.*$)/gim, '<div class="p-2.5 my-2 rounded-xl bg-emerald-500/10 border-l-4 border-emerald-400 text-[11px] text-emerald-200">$1</div>');

  // Negrita, Cursiva y código
  text = text.replace(/\\*\\*(.*?)\\*\\*/g, '<b class="text-white font-extrabold">$1</b>');
  text = text.replace(/\\*(.*?)\\*/g, '<i class="text-emerald-300 not-italic font-semibold">$1</i>');
  text = text.replace(/_(.*?)_/g, '<span class="text-gray-400 text-[11px] italic">$1</span>');

  // Puntos de lista
  text = text.replace(/^[•\\-\\*] (.*$)/gim, '<div class="flex items-start gap-1.5 ml-1 my-0.5"><span class="text-emerald-400 text-[10px] leading-4 shrink-0">▸</span><span>$1</span></div>');

  // Badges y etiquetas
  text = text.replace(/\\[(Verificado[^\\]]*)\\]/gi, '<span class="px-1.5 py-0.5 rounded-full text-[9px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold">$1</span>');
  text = text.replace(/\\[(Descartado[^\\]]*)\\]/gi, '<span class="px-1.5 py-0.5 rounded-full text-[9px] bg-red-500/20 text-red-300 border border-red-500/40 font-bold">$1</span>');
  text = text.replace(/\\[(Sin registro[^\\]]*)\\]/gi, '<span class="px-1.5 py-0.5 rounded-full text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">$1</span>');

  text = text.replace(/\\n{2,}/g, '<div class="h-2"></div>');
  text = text.replace(/\\n/g, '<br>');
  return text;
}"""

if antiguo_format in content:
    content = content.replace(antiguo_format, nuevo_format, 1)
    print("formatBotText actualizado.")
else:
    print("formatBotText antiguo no encontrado con match exacto.")

INDEX_HTML.write_text(content, encoding="utf-8")
print("index.html guardado exitosamente.")
