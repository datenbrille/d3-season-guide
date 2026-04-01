#!/usr/bin/env python3
"""
D3 Season Guide Generator
Generates a static HTML page from YAML data files.

Usage:
    python build.py                     # Uses default build (monk-sunwuko-tr)
    python build.py --build crusader-akkhan

Requirements:
    pip install pyyaml
"""

import argparse
from pathlib import Path
import yaml



def load_yaml(path: Path) -> dict:
    """Load a YAML file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def merge_boss_data(journey: dict, static: dict) -> dict:
    """Merge boss location data from static into journey tasks."""
    bosses = static.get('bosses', {}).get('story_bosses', {})
    keywardens = static.get('keywardens', {})

    for chapter_key in ['chapter_2', 'chapter_3', 'chapter_4']:
        chapter = journey.get(chapter_key, {})
        for task in chapter.get('tasks', []):
            # Merge boss data
            if task.get('type') == 'boss_kill' and task.get('boss'):
                boss_id = task['boss']
                if boss_id in bosses:
                    task['boss_data'] = bosses[boss_id]

            # Merge keywarden data
            if task.get('type') == 'keywarden' and task.get('keywarden'):
                kw_id = task['keywarden']
                if kw_id in keywardens:
                    task['keywarden_data'] = keywardens[kw_id]

    return journey


def generate_html(static: dict, journey: dict, build: dict, start_guide: dict = None, glossary: dict = None) -> str:
    """Generate the complete HTML page."""
    season = journey.get('season', {})
    season_num = season.get('number', '??')
    build_name = build.get('build', {}).get('short_name', 'Unknown')
    build_class = build.get('build', {}).get('class', 'Unknown')

    # Get the set pieces for this class from Haedrig's gifts
    haedrig_gifts = season.get('haedrig_gifts', {})
    class_key = build_class.lower().replace(' ', '_')
    set_name = haedrig_gifts.get(class_key, 'Unknown Set')

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D3 S{season_num} {build_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 10px;
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{ font-size: 1.3em; text-align: center; color: #f4a460; margin-bottom: 10px; }}
        .tabs {{ display: flex; gap: 3px; margin-bottom: 10px; flex-wrap: wrap; }}
        .tab {{
            flex: 1;
            padding: 8px 3px;
            background: #16213e;
            border: none;
            color: #aaa;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.75em;
            min-width: 50px;
        }}
        .tab.active {{ background: #e94560; color: #fff; }}
        .content {{ display: none; }}
        .content.active {{ display: block; }}
        .section {{ background: #16213e; border-radius: 8px; padding: 12px; margin-bottom: 10px; }}
        .section h2 {{ font-size: 1em; color: #f4a460; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 5px; }}
        .section h3 {{ font-size: 0.9em; color: #888; margin: 10px 0 5px 0; }}
        .item {{ display: flex; align-items: center; padding: 6px 0; border-bottom: 1px solid #222; }}
        .item:last-child {{ border-bottom: none; }}
        .item input[type="checkbox"] {{ margin-right: 10px; width: 20px; height: 20px; accent-color: #e94560; }}
        .item label {{ flex: 1; font-size: 0.9em; }}
        .item .diff {{ font-size: 0.75em; color: #888; margin-left: 5px; }}
        .item.checked label {{ text-decoration: line-through; color: #666; }}
        .note {{ font-size: 0.8em; color: #f4a460; margin-top: 5px; font-style: italic; }}
        .gear-checker .stat-checks {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
        .gear-checker .stat-checks label {{
            background: #1a1a2e;
            padding: 6px 10px;
            border-radius: 5px;
            font-size: 0.85em;
            cursor: pointer;
            border: 1px solid #333;
            transition: all 0.2s;
        }}
        .gear-checker .stat-checks label:has(input:checked) {{
            background: #2d5a3d;
            border-color: #4a9;
        }}
        .gear-checker .stat-checks input {{ margin-right: 5px; accent-color: #4a9; }}
        .reroll-advice {{
            background: #2a1a3e;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            border-left: 3px solid #e94560;
            font-size: 0.9em;
        }}
        .reroll-advice.perfect {{ border-left-color: #4a9; background: #1a2e1a; }}
        .reroll-advice.good {{ border-left-color: #f4a460; background: #2e2a1a; }}
        /* Stat Calculator */
        .stat-calculator .stat-inputs {{ display: flex; flex-direction: column; gap: 10px; }}
        .stat-input-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }}
        .stat-input-row label {{ font-size: 0.9em; flex: 1; }}
        .input-with-unit {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .stat-input-row input {{
            width: 80px;
            padding: 8px;
            border: 1px solid #444;
            border-radius: 5px;
            background: #1a1a2e;
            color: #fff;
            font-size: 1em;
            text-align: right;
        }}
        .stat-input-row input:focus {{
            outline: none;
            border-color: #e94560;
        }}
        .input-with-unit span {{ color: #888; font-size: 0.9em; width: 20px; }}
        /* Stat Results */
        .stat-result {{
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }}
        .stat-result .stat-name {{ width: 60px; font-weight: bold; font-size: 0.85em; }}
        .stat-result .stat-bar {{
            flex: 1;
            height: 20px;
            background: #1a1a2e;
            border-radius: 10px;
            overflow: hidden;
            margin: 0 10px;
        }}
        .stat-result .stat-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s, background 0.3s;
            width: 0%;
        }}
        .stat-result .stat-value {{ width: 100px; text-align: right; font-size: 0.85em; }}
        .stat-fill.bad {{ background: linear-gradient(90deg, #e94560, #c73e54); }}
        .stat-fill.ok {{ background: linear-gradient(90deg, #f4a460, #d4843f); }}
        .stat-fill.good {{ background: linear-gradient(90deg, #4a9, #3a8070); }}
        #stat-recommendations {{ min-height: 60px; }}
        #stat-recommendations.has-issues {{ border-left-color: #e94560; background: #2e1a1a; }}
        #stat-recommendations.all-good {{ border-left-color: #4a9; background: #1a2e1a; }}
        .progress {{ background: #333; border-radius: 10px; height: 20px; margin-bottom: 15px; overflow: hidden; }}
        .progress-bar {{ background: linear-gradient(90deg, #e94560, #f4a460); height: 100%; transition: width 0.3s; }}
        .progress-text {{ text-align: center; font-size: 0.8em; margin-top: 3px; color: #888; }}
        .reset {{ background: #333; color: #888; border: none; padding: 8px 15px; border-radius: 5px; margin-top: 10px; cursor: pointer; font-size: 0.8em; }}
        .reward {{ background: #2d4a3e; padding: 8px; border-radius: 5px; margin-top: 8px; font-size: 0.85em; }}
        .reward strong {{ color: #4ade80; }}
        .info-box {{ background: #2a2a4e; padding: 10px; border-radius: 5px; margin: 8px 0; font-size: 0.85em; line-height: 1.5; }}
        .info-box strong {{ color: #f4a460; }}
        .skill-table {{ width: 100%; font-size: 0.85em; border-collapse: collapse; margin-top: 8px; }}
        .skill-table th, .skill-table td {{ padding: 6px 4px; text-align: left; border-bottom: 1px solid #333; }}
        .skill-table th {{ color: #f4a460; background: #1a1a2e; }}
        .skill-table td:first-child {{ color: #888; width: 50px; }}
        .gear-slot {{ display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #222; font-size: 0.85em; }}
        .gear-slot:last-child {{ border-bottom: none; }}
        .gear-slot .slot {{ color: #888; width: 80px; }}
        .gear-slot .item-name {{ flex: 1; color: #eee; }}
        .gear-slot .stats {{ color: #4ade80; font-size: 0.8em; }}
        .cube-slot {{ background: #2d2a4e; padding: 8px; border-radius: 5px; margin: 5px 0; }}
        .cube-slot strong {{ color: #a78bfa; }}
        .paragon-section {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .paragon-box {{ background: #2a2a4e; padding: 10px; border-radius: 5px; }}
        .paragon-box h4 {{ color: #f4a460; font-size: 0.85em; margin-bottom: 5px; }}
        .paragon-box ol {{ margin-left: 15px; font-size: 0.8em; line-height: 1.6; }}
        .altar-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-size: 0.75em; }}
        .altar-item {{ background: #2a2a4e; padding: 5px 8px; border-radius: 3px; }}
        .altar-item span {{ color: #888; }}
        .search-box {{ width: 100%; padding: 10px; border: none; border-radius: 5px; background: #2a2a4e; color: #eee; font-size: 0.9em; margin-bottom: 10px; }}
        .search-box::placeholder {{ color: #666; }}
        .boss-card {{ background: #2a2a4e; padding: 10px; border-radius: 5px; margin-bottom: 8px; }}
        .boss-card.hidden {{ display: none; }}
        .boss-card h4 {{ color: #f4a460; margin-bottom: 5px; }}
        .boss-card .location {{ color: #4ade80; font-size: 0.85em; }}
        .boss-card .waypoint {{ color: #888; font-size: 0.8em; }}
        .boss-card .notes {{ color: #aaa; font-size: 0.8em; margin-top: 5px; font-style: italic; }}
        .act-badge {{ display: inline-block; background: #e94560; color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 5px; }}
    </style>
</head>
<body>
    <h1>{_get_class_emoji(build_class)} {build_name} - S{season_num}</h1>

    <div class="progress"><div class="progress-bar" id="progressBar"></div></div>
    <div class="progress-text" id="progressText">0 / 0</div>

    <div class="tabs">
        <button class="tab active" data-tab="start">Start</button>
        <button class="tab" data-tab="journey">Journey</button>
        <button class="tab" data-tab="build">Build</button>
        <button class="tab" data-tab="gear">Gear</button>
        <button class="tab" data-tab="bosses">Bosses</button>
        <button class="tab" data-tab="altar">Altar</button>
        <button class="tab" data-tab="farm">Farm</button>
        <button class="tab" data-tab="glossary">A-Z</button>
    </div>

    <!-- START TAB -->
    <div id="start" class="content active">
{_generate_start_html(start_guide) if start_guide else '<div class="section"><h2>Season Start Guide</h2><p>Keine Start-Guide Daten gefunden.</p></div>'}
    </div>

    <!-- JOURNEY TAB -->
    <div id="journey" class="content">
{_generate_journey_html(journey, build, set_name)}
    </div>

    <!-- BUILD TAB -->
    <div id="build" class="content">
{_generate_build_html(build)}
    </div>

    <!-- GEAR TAB -->
    <div id="gear" class="content">
{_generate_gear_html(build)}
    </div>

    <!-- BOSSES TAB -->
    <div id="bosses" class="content">
{_generate_bosses_html(static)}
    </div>

    <!-- ALTAR TAB -->
    <div id="altar" class="content">
{_generate_altar_html(static)}
    </div>

    <!-- FARM TAB -->
    <div id="farm" class="content">
{_generate_farm_html(static, build)}
    </div>

    <!-- GLOSSARY TAB -->
    <div id="glossary" class="content">
{_generate_glossary_html(glossary) if glossary else '<div class="section"><h2>Glossar</h2><p>Keine Glossar-Daten.</p></div>'}
    </div>

    <button class="reset" onclick="resetAll()">Alles zurücksetzen</button>

    <script>
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab).classList.add('active');
            }});
        }});

        // Checkbox handling
        function updateProgress() {{
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const checked = document.querySelectorAll('input[type="checkbox"]:checked').length;
            const total = checkboxes.length;
            const percent = Math.round((checked / total) * 100);
            document.getElementById('progressBar').style.width = percent + '%';
            document.getElementById('progressText').textContent = `${{checked}} / ${{total}} (${{percent}}%)`;
        }}

        function saveState() {{
            const state = {{}};
            document.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
                const key = cb.id || (cb.dataset.slot + '_' + cb.dataset.stat);
                if (key) state[key] = cb.checked;
            }});
            localStorage.setItem('d3s{season_num}', JSON.stringify(state));
        }}

        function loadState() {{
            const state = JSON.parse(localStorage.getItem('d3s{season_num}') || '{{}}');
            document.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
                const key = cb.id || (cb.dataset.slot + '_' + cb.dataset.stat);
                if (key && state[key] !== undefined) {{
                    cb.checked = state[key];
                }}
                if (cb.checked) {{
                    cb.closest('.item')?.classList.add('checked');
                }}
            }});
            updateProgress();
            // Update all gear checker advice on load
            ['mh','oh','helm','shoulders','chest','gloves','bracers','belt','pants','boots','ring1','ring2','amulet'].forEach(updateGearAdvice);
        }}

        document.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
            cb.addEventListener('change', () => {{
                cb.closest('.item')?.classList.toggle('checked', cb.checked);
                saveState();
                updateProgress();
            }});
        }});

        function resetAll() {{
            if (confirm('Wirklich alles zurücksetzen?')) {{
                document.querySelectorAll('input[type="checkbox"]').forEach(cb => {{
                    cb.checked = false;
                    cb.closest('.item')?.classList.remove('checked');
                }});
                saveState();
                updateProgress();
            }}
        }}

        // Boss search
        const searchBox = document.getElementById('bossSearch');
        if (searchBox) {{
            searchBox.addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase();
                document.querySelectorAll('.boss-card').forEach(card => {{
                    const text = card.textContent.toLowerCase();
                    card.classList.toggle('hidden', !text.includes(query));
                }});
            }});
        }}

        // Gear Checker Logic
        const gearAdvice = {{
            mh: {{
                priority: ['socket', 'dex', 'dmgpct', 'ad'],
                optional: ['cdr', 'rcr'],
                bad: ['vit', 'lph'],
                socketNote: '⚠️ Socket mit Ramaladnis Gift hinzufügen, NICHT rerolled!',
                getAdvice: (has) => {{
                    if (!has.socket) return {{ text: '🎁 Ramaladnis Gift für Socket nutzen! Dann schlechtesten Stat rerolled.', cls: '' }};
                    if (!has.dex) return {{ text: '❌ Dex fehlt → anderer Stat zu DEX rerolled', cls: '' }};
                    if (!has.dmgpct && (has.vit || has.lph)) return {{ text: '🔄 ' + (has.vit ? 'Vit' : 'LpH') + ' → +10% Damage rerolled', cls: '' }};
                    if (!has.dmgpct && !has.ad) return {{ text: '🔄 Schlechtesten Stat → +10% Damage rerolled', cls: '' }};
                    if (has.vit || has.lph) return {{ text: '🔄 ' + (has.vit ? 'Vit' : 'LpH') + ' → Area Damage rerolled', cls: 'good' }};
                    if (has.socket && has.dex && has.dmgpct && has.ad) return {{ text: '✅ PERFEKT! Nichts rerolled nötig!', cls: 'perfect' }};
                    return {{ text: '👍 Gute Stats! Optional: +AD oder CDR', cls: 'good' }};
                }}
            }},
            oh: {{
                priority: ['socket', 'dex', 'dmgpct', 'ad'],
                getAdvice: (has) => {{
                    if (!has.socket) return {{ text: '🎁 Ramaladnis Gift für Socket nutzen!', cls: '' }};
                    if (!has.dex) return {{ text: '❌ Dex fehlt → rerolled zu DEX', cls: '' }};
                    if (!has.dmgpct && (has.vit || has.lph)) return {{ text: '🔄 ' + (has.vit ? 'Vit' : 'LpH') + ' → +10% Damage', cls: '' }};
                    if (has.vit || has.lph) return {{ text: '🔄 ' + (has.vit ? 'Vit' : 'LpH') + ' → Area Damage', cls: 'good' }};
                    if (has.socket && has.dex && has.dmgpct) return {{ text: '✅ Sehr gut! Optional: AD', cls: 'perfect' }};
                    return {{ text: '👍 Okay Stats', cls: 'good' }};
                }}
            }},
            helm: {{
                priority: ['socket', 'dex', 'chc', 'skill'],
                getAdvice: (has) => {{
                    if (!has.socket) return {{ text: '❌ Socket fehlt! → Reroll zu Socket (für Topaz = RCR!)', cls: '' }};
                    if (!has.dex) return {{ text: '❌ Dex fehlt → rerolled zu DEX', cls: '' }};
                    if (!has.chc && has.allres) return {{ text: '🔄 All Res → CHC 6% rerolled', cls: '' }};
                    if (!has.chc && has.vit) return {{ text: '🔄 Vit → CHC 6% rerolled (Defense woanders holen)', cls: '' }};
                    if (!has.chc) return {{ text: '🔄 Schlechtesten Stat → CHC 6%', cls: '' }};
                    if (has.socket && has.dex && has.chc && has.skill) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    if (has.socket && has.dex && has.chc) return {{ text: '👍 Sehr gut! TR% wäre Bonus', cls: 'good' }};
                    return {{ text: '👍 Okay', cls: 'good' }};
                }}
            }},
            shoulders: {{
                priority: ['dex', 'rcr', 'cdr', 'ad'],
                getAdvice: (has) => {{
                    if (!has.dex) return {{ text: '❌ Dex fehlt → rerolled', cls: '' }};
                    if (!has.rcr && has.life) return {{ text: '🔄 Life% → RCR 8% (Spirit Management!)', cls: '' }};
                    if (!has.rcr && !has.cdr) return {{ text: '🔄 Defensiven Stat → RCR 8% oder CDR 8%', cls: '' }};
                    if (has.dex && has.rcr && has.cdr && has.ad) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    if (has.dex && (has.rcr || has.cdr)) return {{ text: '👍 Gut! Vit/AllRes okay für Defense', cls: 'good' }};
                    return {{ text: '👍 Okay', cls: 'good' }};
                }}
            }},
            chest: {{
                priority: ['sockets', 'dex', 'vit', 'allres'],
                getAdvice: (has) => {{
                    if (!has.sockets) return {{ text: '❌ 3 Sockets fehlen! → Reroll!', cls: '' }};
                    if (!has.dex) return {{ text: '❌ Dex fehlt → rerolled', cls: '' }};
                    if (!has.vit) return {{ text: '🔄 Schlechtesten Stat → Vit', cls: '' }};
                    if (!has.allres && !has.elite && has.life) return {{ text: '🔄 Life% → All Res oder Elite DR%', cls: '' }};
                    if (has.sockets && has.dex && has.vit && (has.allres || has.elite)) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    return {{ text: '👍 Gut! Chest ist defensiv', cls: 'good' }};
                }}
            }},
            gloves: {{
                priority: ['dex', 'chc', 'chd', 'rcr'],
                getAdvice: (has) => {{
                    if (!has.dex) return {{ text: '❌ Dex fehlt!', cls: '' }};
                    if (!has.chc && !has.chd) return {{ text: '❌ CHC UND CHD fehlen! Gloves sind OFFENSIV! → CHC rerolled', cls: '' }};
                    if (!has.chc) return {{ text: '🔄 Schlechtesten Stat → CHC 10%', cls: '' }};
                    if (!has.chd && has.vit) return {{ text: '🔄 Vit → CHD 50% (Gloves = Offense!)', cls: '' }};
                    if (!has.chd) return {{ text: '🔄 Schlechtesten Stat → CHD 50%', cls: '' }};
                    if (has.dex && has.chc && has.chd && (has.rcr || has.ad)) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    if (has.dex && has.chc && has.chd) return {{ text: '👍 Core Stats da! 4. Stat: RCR/AD ideal', cls: 'good' }};
                    return {{ text: '👍 Okay', cls: 'good' }};
                }}
            }},
            bracers: {{
                priority: ['ele', 'chc', 'dex', 'vit'],
                getAdvice: (has) => {{
                    if (!has.ele && !has.chc) return {{ text: '❌ Cold% UND CHC fehlen! → Cold% 20% rerolled (riesiger DMG Boost!)', cls: '' }};
                    if (!has.ele) return {{ text: '🔄 Schlechtesten Stat → Cold% 20% (WICHTIG!)', cls: '' }};
                    if (!has.chc) return {{ text: '🔄 Schlechtesten Stat → CHC 6%', cls: '' }};
                    if (!has.dex) return {{ text: '🔄 → Dex', cls: '' }};
                    if (has.ele && has.chc && has.dex && (has.vit || has.lph)) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    return {{ text: '👍 Gut!', cls: 'good' }};
                }}
            }},
            belt: {{
                priority: ['dex', 'vit', 'allres', 'life'],
                getAdvice: (has) => {{
                    if (!has.dex) return {{ text: '❌ Dex fehlt', cls: '' }};
                    if (!has.vit) return {{ text: '🔄 → Vit', cls: '' }};
                    if (!has.allres && !has.life) return {{ text: '🔄 Schlechtesten → All Res oder Life%', cls: '' }};
                    if (has.dex && has.vit && has.allres) return {{ text: '✅ PERFEKT! Belt ist rein defensiv', cls: 'perfect' }};
                    return {{ text: '👍 Gut! Belt = Defense', cls: 'good' }};
                }}
            }},
            pants: {{
                priority: ['sockets', 'dex', 'vit', 'allres'],
                getAdvice: (has) => {{
                    if (!has.sockets) return {{ text: '❌ 2 Sockets fehlen!', cls: '' }};
                    if (!has.dex) return {{ text: '❌ Dex fehlt', cls: '' }};
                    if (!has.vit) return {{ text: '🔄 → Vit', cls: '' }};
                    if (!has.allres && !has.armor) return {{ text: '🔄 → All Res oder Armor', cls: '' }};
                    if (has.sockets && has.dex && has.vit && has.allres) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    return {{ text: '👍 Gut! Pants = Defense', cls: 'good' }};
                }}
            }},
            boots: {{
                priority: ['dex', 'vit', 'skill', 'allres'],
                getAdvice: (has) => {{
                    if (!has.dex) return {{ text: '❌ Dex fehlt', cls: '' }};
                    if (has.ms) return {{ text: '🔄 Movement Speed → TR% 15%! (MS aus Paragon!)', cls: '' }};
                    if (!has.skill) return {{ text: '🔄 Schlechtesten Stat → TR% 15% (mehr Damage!)', cls: '' }};
                    if (!has.vit) return {{ text: '🔄 → Vit', cls: '' }};
                    if (has.dex && has.vit && has.skill && has.allres) return {{ text: '✅ PERFEKT!', cls: 'perfect' }};
                    return {{ text: '👍 Gut!', cls: 'good' }};
                }}
            }},
            ring1: {{
                priority: ['socket', 'chc', 'chd', 'dex'],
                getAdvice: (has) => {{
                    if (!has.socket) return {{ text: '❌ Socket fehlt! → IMMER zuerst Socket rerolled!', cls: '' }};
                    if (!has.chc && !has.chd) return {{ text: '🔄 → CHC oder CHD', cls: '' }};
                    if (has.socket && has.chc && has.chd) return {{ text: '✅ Top Stats! Dex/AD wäre Bonus', cls: 'perfect' }};
                    if (has.socket && (has.chc || has.chd)) return {{ text: '👍 Okay, Socket + 1 Crit Stat', cls: 'good' }};
                    return {{ text: '👍 Socket da = nutzbar', cls: 'good' }};
                }}
            }},
            ring2: {{
                priority: ['socket', 'chc', 'chd', 'dex'],
                getAdvice: (has) => {{
                    if (!has.socket) return {{ text: '❌ Socket fehlt! → IMMER zuerst Socket!', cls: '' }};
                    if (!has.chc && !has.chd) return {{ text: '🔄 → CHC oder CHD', cls: '' }};
                    if (has.socket && has.chc && has.chd) return {{ text: '✅ Top Stats!', cls: 'perfect' }};
                    if (has.socket && (has.chc || has.chd)) return {{ text: '👍 Okay', cls: 'good' }};
                    return {{ text: '👍 Socket da = nutzbar', cls: 'good' }};
                }}
            }},
            amulet: {{
                priority: ['socket', 'ele', 'chc', 'chd'],
                getAdvice: (has) => {{
                    if (!has.socket) return {{ text: '❌ Socket fehlt! → IMMER zuerst Socket für Legendary Gem!', cls: '' }};
                    if (!has.ele && !has.chc && !has.chd) return {{ text: '🔄 → Cold% 20% (bester Stat für Ammy!)', cls: '' }};
                    if (!has.chc && !has.chd) return {{ text: '🔄 → CHC 10% oder CHD 100%', cls: '' }};
                    if (has.socket && has.ele && has.chc && has.chd) return {{ text: '✅ PERFEKT! Traumhaftes Amulet!', cls: 'perfect' }};
                    if (has.socket && ((has.ele && has.chc) || (has.ele && has.chd) || (has.chc && has.chd))) return {{ text: '👍 Sehr gut! 3 gute Stats', cls: 'good' }};
                    return {{ text: '👍 Socket da = nutzbar', cls: 'good' }};
                }}
            }}
        }};

        function updateGearAdvice(slot) {{
            const checks = document.querySelectorAll(`[data-slot="${{slot}}"]`);
            const has = {{}};
            checks.forEach(cb => {{ has[cb.dataset.stat] = cb.checked; }});

            const adviceEl = document.getElementById(`advice-${{slot}}`);
            if (adviceEl && gearAdvice[slot]) {{
                const result = gearAdvice[slot].getAdvice(has);
                adviceEl.textContent = result.text;
                adviceEl.className = 'reroll-advice ' + (result.cls || '');
            }}
        }}

        document.querySelectorAll('.gear-checker input[type="checkbox"]').forEach(cb => {{
            cb.addEventListener('change', () => {{
                updateGearAdvice(cb.dataset.slot);
            }});
        }});

        // Stat Calculator Logic
        const statBreakpoints = {{
            cdr: {{ min: 45, good: 50, perfect: 55, max: 80, unit: '%' }},
            rcr: {{ min: 40, good: 50, perfect: 55, max: 80, unit: '%' }},
            chc: {{ min: 40, good: 50, perfect: 55, max: 65, unit: '%' }},
            chd: {{ min: 350, good: 450, perfect: 500, max: 600, unit: '%' }},
            cold: {{ min: 20, good: 40, perfect: 40, max: 40, unit: '%' }},
            ad: {{ min: 50, good: 100, perfect: 130, max: 150, unit: '%' }}
        }};

        const statNames = {{
            cdr: 'CDR',
            rcr: 'RCR',
            chc: 'CHC',
            chd: 'CHD',
            cold: 'Cold%',
            ad: 'Area Damage'
        }};

        const statTips = {{
            cdr: {{
                low: 'CDR zu niedrig! Epiphany hat keine Uptime. → CDR auf Shoulders, Gloves, Rings, Amulet, Paragon',
                ok: 'CDR okay, aber mehr wäre besser für Epiphany Uptime',
                good: 'CDR perfekt! Epiphany hat fast 100% Uptime'
            }},
            rcr: {{
                low: 'RCR zu niedrig! Spirit Probleme! → Topaz in Helm, RCR auf Shoulders/Gloves, Paragon',
                ok: 'RCR okay, evtl. noch Spirit Probleme bei langen Fights',
                good: 'RCR perfekt! Smooth Tempest Rush'
            }},
            chc: {{
                low: 'CHC zu niedrig! Damage sehr inkonsistent. → CHC auf Helm, Gloves, Bracers, Rings, Amulet',
                ok: 'CHC okay, Damage ist consistent genug',
                good: 'CHC perfekt! Crits überall'
            }},
            chd: {{
                low: 'CHD zu niedrig! Crits sind schwach. → CHD auf Gloves, Rings, Amulet + Emeralds in Weapons',
                ok: 'CHD okay, guter Crit Damage',
                good: 'CHD perfekt! Fette Crits!'
            }},
            cold: {{
                low: 'Cold% fehlt! → Cold% auf Bracers (20%) und Amulet (20%)',
                ok: 'Cold% nur auf einem Slot. Amulet oder Bracers fehlt',
                good: 'Cold% perfekt! Max aus Bracers + Amulet'
            }},
            ad: {{
                low: 'Area Damage niedrig. → AD auf Shoulders, Gloves, Rings, Weapons, Paragon',
                ok: 'Area Damage okay für AoE',
                good: 'Area Damage perfekt! Explosive AoE Kills'
            }}
        }};

        function updateStatCalculator() {{
            const stats = ['cdr', 'rcr', 'chc', 'chd', 'cold', 'ad'];
            const recommendations = [];
            let allGood = true;

            stats.forEach(stat => {{
                const input = document.getElementById(`stat-${{stat}}`);
                const fill = document.getElementById(`fill-${{stat}}`);
                const value = document.getElementById(`value-${{stat}}`);
                const bp = statBreakpoints[stat];

                if (!input || !fill || !value) return;

                const val = parseFloat(input.value) || 0;
                const percent = Math.min(100, (val / bp.max) * 100);

                fill.style.width = percent + '%';

                let status, cls;
                if (val < bp.min) {{
                    status = '❌ Niedrig';
                    cls = 'bad';
                    recommendations.push(statTips[stat].low);
                    allGood = false;
                }} else if (val < bp.good) {{
                    status = '⚠️ Okay';
                    cls = 'ok';
                    if (stat !== 'cold' && stat !== 'ad') {{
                        recommendations.push(statTips[stat].ok);
                    }}
                }} else if (val >= bp.perfect) {{
                    status = '✅ Perfekt';
                    cls = 'good';
                }} else {{
                    status = '👍 Gut';
                    cls = 'good';
                }}

                fill.className = `stat-fill ${{cls}}`;
                value.textContent = val > 0 ? `${{val}}${{bp.unit}} - ${{status}}` : '-';

                // Save to localStorage
                localStorage.setItem(`stat_${{stat}}`, val);
            }});

            const recEl = document.getElementById('stat-recommendations');
            if (recEl) {{
                if (recommendations.length === 0) {{
                    recEl.innerHTML = '✅ <strong>Alle Stats sind gut!</strong><br><br>Dein Build ist solide. Fokus jetzt auf:<br>• Ancient Gear farmen<br>• Augments hinzufügen<br>• Paragon leveln';
                    recEl.className = 'info-box all-good';
                }} else {{
                    recEl.innerHTML = '<strong>🔧 Verbesserungen:</strong><br><br>' + recommendations.map(r => '• ' + r).join('<br><br>');
                    recEl.className = 'info-box has-issues';
                }}
            }}
        }}

        function loadStatCalculator() {{
            ['cdr', 'rcr', 'chc', 'chd', 'cold', 'ad'].forEach(stat => {{
                const saved = localStorage.getItem(`stat_${{stat}}`);
                const input = document.getElementById(`stat-${{stat}}`);
                if (saved && input) {{
                    input.value = saved;
                }}
            }});
            updateStatCalculator();
        }}

        // Add listeners to stat inputs
        ['cdr', 'rcr', 'chc', 'chd', 'cold', 'ad'].forEach(stat => {{
            const input = document.getElementById(`stat-${{stat}}`);
            if (input) {{
                input.addEventListener('input', updateStatCalculator);
            }}
        }});

        loadStatCalculator();
        loadState();
    </script>
</body>
</html>'''

    return html


def _get_class_emoji(class_name: str) -> str:
    """Return an emoji for the class."""
    emojis = {
        'monk': '🐵',
        'barbarian': '⚔️',
        'crusader': '🛡️',
        'demon hunter': '🏹',
        'necromancer': '💀',
        'witch doctor': '🧙',
        'wizard': '🔮',
    }
    return emojis.get(class_name.lower(), '🎮')


def _generate_journey_html(journey: dict, build: dict, set_name: str) -> str:
    """Generate the Journey tab HTML."""
    html_parts = []

    # Chapter 2
    ch2 = journey.get('chapter_2', {})
    html_parts.append(f'''        <div class="section">
            <h2>Chapter II → Haedrig #1</h2>
            <div class="reward"><strong>Reward:</strong> {set_name} 2pc</div>''')

    for i, task in enumerate(ch2.get('tasks', []), 1):
        task_html = _generate_task_html(f'j{i}', task)
        html_parts.append(task_html)
    html_parts.append('        </div>')

    # Chapter 3
    ch3 = journey.get('chapter_3', {})
    html_parts.append(f'''
        <div class="section">
            <h2>Chapter III → Haedrig #2</h2>
            <div class="reward"><strong>Reward:</strong> {set_name} 4pc</div>''')

    for i, task in enumerate(ch3.get('tasks', []), 20):
        task_html = _generate_task_html(f'j{i}', task)
        html_parts.append(task_html)
    html_parts.append('        </div>')

    # Chapter 4
    ch4 = journey.get('chapter_4', {})
    html_parts.append(f'''
        <div class="section">
            <h2>Chapter IV → Haedrig #3</h2>
            <div class="reward"><strong>Reward:</strong> {set_name} 6pc</div>''')

    for i, task in enumerate(ch4.get('tasks', []), 40):
        task_html = _generate_task_html(f'j{i}', task)
        html_parts.append(task_html)
    html_parts.append('        </div>')

    return '\n'.join(html_parts)


def _generate_task_html(task_id: str, task: dict) -> str:
    """Generate HTML for a single task."""
    name = task.get('name', 'Unknown')
    difficulty = task.get('difficulty', '')

    # Add location info for boss kills
    location_info = ''
    if task.get('boss_data'):
        bd = task['boss_data']
        location_info = f" - A{bd.get('act', '?')}: {bd.get('location', '')}"
    elif task.get('keywarden_data'):
        kd = task['keywarden_data']
        location_info = f" - A{kd.get('act', '?')}: {kd.get('location', '')}"

    diff_html = f'<span class="diff">({difficulty}){location_info}</span>' if difficulty else ''
    if location_info and not difficulty:
        diff_html = f'<span class="diff">{location_info}</span>'

    milestone = '⭐ ' if task.get('milestone') else ''

    return f'''            <div class="item"><input type="checkbox" id="{task_id}"><label for="{task_id}">{milestone}{name} {diff_html}</label></div>'''


def _generate_build_html(build: dict) -> str:
    """Generate the Build tab HTML."""
    skills = build.get('skills', {})
    active = skills.get('active', [])
    passives = skills.get('passives', {})
    gems = build.get('legendary_gems', {})
    cube = build.get('kanais_cube', {})
    paragon = build.get('paragon', {})
    gameplay = build.get('gameplay', {})

    # Active Skills Table
    skill_rows = ''
    for s in active:
        slot = s.get('slot', '?')
        skill = s.get('skill', '?')
        rune = s.get('rune', '?')
        skill_rows += f'''                <tr><td>{slot}</td><td><strong>{skill}</strong></td><td>{rune}</td></tr>\n'''

    # Passives
    passive_html = ''
    for i, p in enumerate(passives.get('required', []) + passives.get('recommended', []), 1):
        passive_html += f'''                <strong>{i}. {p.get('name', '?')}</strong> - {p.get('effect', '')}<br>\n'''

    # Gems
    gem_items = ''
    for i, g in enumerate(gems.get('required', []) + gems.get('pushing', [])[:1], 1):
        gem_items += f'''            <div class="item"><input type="checkbox" id="lg{i}"><label for="lg{i}"><strong>{g.get('name', '?')}</strong> - {g.get('notes', '')}</label></div>\n'''

    # Paragon
    paragon_html = ''
    for cat in ['core', 'offense', 'defense', 'utility']:
        cat_data = paragon.get(cat, {})
        # Try both int and string keys (YAML parses as int)
        items = ''
        for i in range(1, 5):
            val = cat_data.get(i) or cat_data.get(str(i)) or '?'
            items += f'<li>{val}</li>'
        paragon_html += f'''                <div class="paragon-box">
                    <h4>{cat.title()}</h4>
                    <ol>{items}</ol>
                </div>\n'''

    # Gameplay Rotation
    rotation = gameplay.get('rotation', [])
    rotation_html = ''
    for step in rotation:
        num = step.get('step', '?')
        action = step.get('action', '')
        notes = step.get('notes', '')
        rotation_html += f'<strong>{num}.</strong> {action}<br><span style="color:#888;font-size:0.85em">{notes}</span><br>\n'

    tips = gameplay.get('tips', [])
    tips_html = ''.join([f'<li>{tip}</li>' for tip in tips])

    return f'''        <div class="section">
            <h2>Active Skills</h2>
            <table class="skill-table">
                <tr><th>Slot</th><th>Skill</th><th>Rune</th></tr>
{skill_rows}            </table>
        </div>

        <div class="section">
            <h2>Passive Skills</h2>
            <div class="info-box">
{passive_html}            </div>
        </div>

        <div class="section">
            <h2>Legendary Gems</h2>
{gem_items}        </div>

        <div class="section">
            <h2>Kanai's Cube</h2>
            <div class="cube-slot"><strong>Weapon:</strong> {cube.get('weapon', {}).get('item', '?')} - {cube.get('weapon', {}).get('power', '')}</div>
            <div class="cube-slot"><strong>Armor:</strong> {(cube.get('armor', {}).get('primary') or cube.get('armor', {})).get('item', '?')} - {(cube.get('armor', {}).get('primary') or cube.get('armor', {})).get('notes', '')}</div>
            <div class="cube-slot"><strong>Jewelry:</strong> {cube.get('jewelry', {}).get('item', '?')} - {cube.get('jewelry', {}).get('power', '')}</div>
        </div>

        <div class="section">
            <h2>Paragon Points</h2>
            <div class="paragon-section">
{paragon_html}            </div>
        </div>

        <div class="section">
            <h2>🎮 Gameplay Rotation</h2>
            <div class="info-box">
{rotation_html}            </div>
        </div>

        <div class="section">
            <h2>💡 Tipps</h2>
            <ul style="margin-left: 15px; font-size: 0.9em; line-height: 1.6;">
{tips_html}            </ul>
        </div>

        <div class="section">
            <h2>💀 Ich sterbe zu oft!</h2>
            <div class="info-box">
                <strong>Schnelle Fixes:</strong><br>
                • Schwierigkeit runter (kein Shame!)<br>
                • Epiphany aktiv halten (50% DR!)<br>
                • Nicht stehen bleiben - TR = beweglich bleiben!<br>
                • Lefebvre's Soliloquy Buff checken (aktiv?)
            </div>
        </div>

        <div class="section">
            <h2>🛡️ Toughness verbessern</h2>
            <div class="info-box">
                <strong>1. Defensive Stats auf richtigen Slots:</strong><br>
                → Vit auf: Helm, Chest, Belt, Pants, Boots<br>
                → All Res auf: Chest, Belt, Pants, Boots<br>
                → Armor auf: Shoulders, Chest, Belt<br><br>

                <strong>2. Paragon Points:</strong><br>
                → Defense Tab: Resist All zuerst!<br>
                → Dann Life%, Armor, Life Regen<br><br>

                <strong>3. Legendary Gems:</strong><br>
                → Esoteric Alteration (All Res + DR unter 50% HP)<br>
                → Molten Wildebeest's Gizzard (Shield)<br>
                → ⚠️ Ersetzt einen Damage Gem!<br><br>

                <strong>4. Skills/Passives checken:</strong><br>
                → Epiphany IMMER aktiv (50% Damage Reduction!)<br>
                → Mantra of Salvation + Agility Rune<br>
                → Sixth Sense Passive (+25% Armor von Dex)<br>
                → Near Death Experience (Cheat Death)<br><br>

                <strong>5. Gear Cube Powers:</strong><br>
                → Lefebvre's Soliloquy (Cyclone Strike = 50% DR)<br>
                → Spirit Guards Bracers (Spirit Gen = 60% DR)
            </div>
            <p class="note">💡 Monk hat VIEL Damage Reduction - aber nur wenn Buffs aktiv sind!</p>
        </div>

        <div class="section">
            <h2>⚡ Spirit geht aus!</h2>
            <div class="info-box">
                <strong>Das Problem verstehen:</strong><br>
                Tempest Rush kostet Spirit pro Sekunde.<br>
                Ohne genug RCR/Spirit Regen = leer = kein Damage!
            </div>
        </div>

        <div class="section">
            <h2>🔋 Spirit Management Fixes</h2>
            <div class="info-box">
                <strong>1. RCR (Resource Cost Reduction) stapeln:</strong><br>
                → Shoulders: bis zu 8% RCR<br>
                → Gloves: bis zu 8% RCR<br>
                → Rings: bis zu 8% RCR<br>
                → Amulet: bis zu 8% RCR<br>
                → Captain Crimson Set: 20% CDR → auch RCR!<br>
                → Paragon: 10% RCR (Offense Tab)<br><br>

                <strong>2. Spirit Regen erhöhen:</strong><br>
                → Templar Follower: Spirit Regen Buff!<br>
                → Exalted Soul Passive: +100 Max Spirit, +2/s Regen<br>
                → Air Ally: Spirit Regen + Active für Burst<br><br>

                <strong>3. Epiphany uptime!</strong><br>
                → Epiphany gibt Spirit Regen<br>
                → Inner Fire Rune = mehr Regen<br>
                → CDR erhöhen für mehr Uptime<br><br>

                <strong>4. Helm Socket:</strong><br>
                → <strong>Topaz</strong> = 12.5% RCR! (Nicht Diamond!)<br>
                → Das ist RIESIG für Spirit!<br><br>

                <strong>5. Gameplay anpassen:</strong><br>
                → Nicht in leere Räume rushen<br>
                → Mobs = Damage = overkill Spirit zurück<br>
                → Balance zwischen Speed und Density
            </div>
        </div>

        <div class="section">
            <h2>📊 RCR Breakpoints</h2>
            <div class="info-box">
                <strong>Ziel: 50%+ RCR für smooth TR</strong><br><br>
                Captain Crimson: ~20%<br>
                Paragon: 10%<br>
                Topaz Helm: 12.5%<br>
                1x Gear Slot: 8%<br>
                <strong>= ~50% RCR</strong><br><br>
                → Wenn immer noch Probleme: 2. Gear Slot mit RCR
            </div>
        </div>

        <div class="section">
            <h2>🔢 Build Stat Calculator</h2>
            <p class="note">Trage deine aktuellen Stats ein (aus Details-Tab im Spiel) und sieh was du verbessern musst!</p>
        </div>

        <div class="section stat-calculator">
            <h2>Deine Stats</h2>
            <div class="stat-inputs">
                <div class="stat-input-row">
                    <label for="stat-cdr">CDR (Cooldown Reduction)</label>
                    <div class="input-with-unit">
                        <input type="number" id="stat-cdr" step="0.1" min="0" max="100" placeholder="z.B. 50">
                        <span>%</span>
                    </div>
                </div>
                <div class="stat-input-row">
                    <label for="stat-rcr">RCR (Resource Cost Reduction)</label>
                    <div class="input-with-unit">
                        <input type="number" id="stat-rcr" step="0.1" min="0" max="100" placeholder="z.B. 43.3">
                        <span>%</span>
                    </div>
                </div>
                <div class="stat-input-row">
                    <label for="stat-chc">CHC (Critical Hit Chance)</label>
                    <div class="input-with-unit">
                        <input type="number" id="stat-chc" step="0.1" min="0" max="100" placeholder="z.B. 45">
                        <span>%</span>
                    </div>
                </div>
                <div class="stat-input-row">
                    <label for="stat-chd">CHD (Critical Hit Damage)</label>
                    <div class="input-with-unit">
                        <input type="number" id="stat-chd" step="1" min="0" max="1000" placeholder="z.B. 450">
                        <span>%</span>
                    </div>
                </div>
                <div class="stat-input-row">
                    <label for="stat-cold">Cold Damage %</label>
                    <div class="input-with-unit">
                        <input type="number" id="stat-cold" step="1" min="0" max="100" placeholder="z.B. 40">
                        <span>%</span>
                    </div>
                </div>
                <div class="stat-input-row">
                    <label for="stat-ad">Area Damage</label>
                    <div class="input-with-unit">
                        <input type="number" id="stat-ad" step="1" min="0" max="200" placeholder="z.B. 100">
                        <span>%</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Auswertung</h2>
            <div id="stat-results">
                <div class="stat-result" id="result-cdr">
                    <span class="stat-name">CDR</span>
                    <span class="stat-bar"><span class="stat-fill" id="fill-cdr"></span></span>
                    <span class="stat-value" id="value-cdr">-</span>
                </div>
                <div class="stat-result" id="result-rcr">
                    <span class="stat-name">RCR</span>
                    <span class="stat-bar"><span class="stat-fill" id="fill-rcr"></span></span>
                    <span class="stat-value" id="value-rcr">-</span>
                </div>
                <div class="stat-result" id="result-chc">
                    <span class="stat-name">CHC</span>
                    <span class="stat-bar"><span class="stat-fill" id="fill-chc"></span></span>
                    <span class="stat-value" id="value-chc">-</span>
                </div>
                <div class="stat-result" id="result-chd">
                    <span class="stat-name">CHD</span>
                    <span class="stat-bar"><span class="stat-fill" id="fill-chd"></span></span>
                    <span class="stat-value" id="value-chd">-</span>
                </div>
                <div class="stat-result" id="result-cold">
                    <span class="stat-name">Cold%</span>
                    <span class="stat-bar"><span class="stat-fill" id="fill-cold"></span></span>
                    <span class="stat-value" id="value-cold">-</span>
                </div>
                <div class="stat-result" id="result-ad">
                    <span class="stat-name">AD</span>
                    <span class="stat-bar"><span class="stat-fill" id="fill-ad"></span></span>
                    <span class="stat-value" id="value-ad">-</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>💡 Empfehlungen</h2>
            <div id="stat-recommendations" class="info-box">
                Trage oben deine Stats ein...
            </div>
        </div>

        <div class="section">
            <h2>📖 Breakpoints für Sunwuko TR</h2>
            <div class="info-box">
                <strong>CDR (Cooldown Reduction):</strong><br>
                • <span style="color:#e94560">Minimum: 45%</span> - Epiphany alle ~13s<br>
                • <span style="color:#f4a460">Gut: 50%</span> - Epiphany alle ~11s<br>
                • <span style="color:#4a9">Perfekt: 55%+</span> - Fast permanente Uptime<br><br>

                <strong>RCR (Resource Cost Reduction):</strong><br>
                • <span style="color:#e94560">Minimum: 40%</span> - Spirit Probleme möglich<br>
                • <span style="color:#f4a460">Gut: 50%</span> - Smooth Channeling<br>
                • <span style="color:#4a9">Perfekt: 55%+</span> - Nie Spirit Probleme<br><br>

                <strong>CHC (Critical Hit Chance):</strong><br>
                • <span style="color:#e94560">Minimum: 40%</span> - Damage inconsistent<br>
                • <span style="color:#f4a460">Gut: 50%</span> - Solide Crits<br>
                • <span style="color:#4a9">Perfekt: 55%+</span> - Sehr consistent<br><br>

                <strong>CHD (Critical Hit Damage):</strong><br>
                • <span style="color:#e94560">Minimum: 350%</span> - Wenig Burst<br>
                • <span style="color:#f4a460">Gut: 450%</span> - Solider Damage<br>
                • <span style="color:#4a9">Perfekt: 500%+</span> - Fette Crits<br><br>

                <strong>Cold Damage %:</strong><br>
                • <span style="color:#e94560">Minimum: 20%</span> - Nur Bracers<br>
                • <span style="color:#f4a460">Gut: 40%</span> - Bracers + Ammy<br>
                • <span style="color:#4a9">Perfekt: 40%</span> - Max (2 Slots)<br><br>

                <strong>Area Damage:</strong><br>
                • <span style="color:#e94560">Minimum: 50%</span> - Basis<br>
                • <span style="color:#f4a460">Gut: 100%</span> - Solide AoE<br>
                • <span style="color:#4a9">Perfekt: 130%+</span> - Max AoE
            </div>
        </div>'''


def _generate_gear_html(build: dict) -> str:
    """Generate the Gear tab HTML."""
    gear = build.get('gear', {}).get('worn', {})

    slots_html = ''
    for slot_name, slot_data in gear.items():
        item = slot_data.get('item', '?')
        stats = slot_data.get('stats_priority', [])[:3]
        stats_str = ', '.join(stats) if stats else ''
        display_slot = slot_name.replace('_', ' ').title()
        slots_html += f'''            <div class="gear-slot">
                <span class="slot">{display_slot}</span>
                <span class="item-name">{item}</span>
                <span class="stats">{stats_str}</span>
            </div>\n'''

    return f'''        <div class="section">
            <h2>Gear Slots</h2>
{slots_html}        </div>

        <div class="section">
            <h2>🔧 Gear verbessern (Paragon 300+)</h2>
            <p class="note">Priorität: 1. Richtige Items → 2. Richtige Stats → 3. Ancient → 4. Augment</p>
        </div>

        <div class="section">
            <h2>1. Enchanting (Mystic)</h2>
            <div class="info-box">
                <strong>Was ist das?</strong><br>
                Bei der Mystic kannst du EINEN Stat auf einem Item neu würfeln.<br>
                Der alte Stat wird durch einen zufälligen neuen ersetzt.
            </div>
        </div>

        <div class="section">
            <h2>📋 Enchanting Schritt-für-Schritt</h2>
            <div class="info-box">
                <strong>Schritt 1:</strong> Zur Mystic gehen (in jeder Stadt)<br><br>
                <strong>Schritt 2:</strong> "Enchant" wählen<br><br>
                <strong>Schritt 3:</strong> Item reinlegen<br><br>
                <strong>Schritt 4:</strong> Stat zum Reroll auswählen<br>
                → ⚠️ Dieser Stat ist PERMANENT markiert!<br>
                → Du kannst später NUR diesen Stat rerolled<br><br>
                <strong>Schritt 5:</strong> Aus 2 Optionen wählen<br>
                → Oder "Keep Original" behalten<br><br>
                <strong>Schritt 6:</strong> Wiederholen bis perfekter Roll
            </div>
            <p class="note">⚠️ WICHTIG: Einmal gewählt, kannst du nur noch DIESEN Stat ändern!</p>
        </div>

        <div class="section">
            <h2>📖 Stat-Namen im Spiel (Mystic)</h2>
            <div class="info-box">
                <strong>Abkürzungen → Echter Name im Spiel:</strong><br><br>
                <table style="width:100%; font-size:0.9em;">
                    <tr><td><strong>All Res</strong></td><td>→ "Resistance to All Elements"</td></tr>
                    <tr><td><strong>CHC</strong></td><td>→ "Critical Hit Chance"</td></tr>
                    <tr><td><strong>CHD</strong></td><td>→ "Critical Hit Damage"</td></tr>
                    <tr><td><strong>CDR</strong></td><td>→ "Cooldown Reduction"</td></tr>
                    <tr><td><strong>RCR</strong></td><td>→ "Resource Cost Reduction"</td></tr>
                    <tr><td><strong>AD</strong></td><td>→ "Area Damage"</td></tr>
                    <tr><td><strong>IAS / AS</strong></td><td>→ "Attack Speed" oder "Attacks per Second"</td></tr>
                    <tr><td><strong>Vit</strong></td><td>→ "Vitality"</td></tr>
                    <tr><td><strong>LpH</strong></td><td>→ "Life per Hit"</td></tr>
                    <tr><td><strong>LpS</strong></td><td>→ "Life Regeneration" oder "Regenerates X Life per Second"</td></tr>
                    <tr><td><strong>Elite DR</strong></td><td>→ "Reduces damage from elites by X%"</td></tr>
                    <tr><td><strong>Cold%</strong></td><td>→ "Cold skills deal X% more damage"</td></tr>
                    <tr><td><strong>TR%</strong></td><td>→ "Tempest Rush deals X% more damage"</td></tr>
                </table>
            </div>
            <p class="note">💡 Bei der Mystic: Scroll durch die Liste um den Stat zu finden!</p>
        </div>

        <div class="section">
            <h2>🛡️ Defensive Stats - Was behalten?</h2>
            <div class="info-box">
                <strong>Resistenzen:</strong><br>
                ✅ <strong>"Resistance to All Elements"</strong> = SEHR GUT<br>
                &nbsp;&nbsp;&nbsp;→ Schützt gegen ALLE Damage-Typen<br><br>
                ❌ <strong>"Arcane/Poison/Fire/etc. Resistance"</strong> = SCHLECHT<br>
                &nbsp;&nbsp;&nbsp;→ Schützt nur gegen 1 von 6 Elementen<br>
                &nbsp;&nbsp;&nbsp;→ IMMER zu "Resistance to All Elements" rerolled!
            </div>
        </div>

        <div class="section">
            <h2>❤️ Life Stats - Priorität</h2>
            <div class="info-box">
                <strong>Von BEST zu WORST:</strong><br><br>
                1️⃣ <strong>Vitality</strong> = BEHALTEN ✅<br>
                &nbsp;&nbsp;&nbsp;→ Mehr HP = mehr EHP<br>
                &nbsp;&nbsp;&nbsp;→ Skaliert mit Life% Bonus<br>
                &nbsp;&nbsp;&nbsp;→ Sehr wertvoll!<br><br>
                2️⃣ <strong>Life per Hit</strong> = SITUATIV 🔄<br>
                &nbsp;&nbsp;&nbsp;→ Heilt X HP pro Hit den du machst<br>
                &nbsp;&nbsp;&nbsp;→ Gut wenn du viele Hits machst<br>
                &nbsp;&nbsp;&nbsp;→ Für TR Monk: okay auf Bracers, nicht kritisch<br><br>
                3️⃣ <strong>Life Regeneration</strong> = IMMER REROLLED ❌<br>
                &nbsp;&nbsp;&nbsp;→ Heilt ~10.000 HP pro Sekunde<br>
                &nbsp;&nbsp;&nbsp;→ Dein HP: 500.000+<br>
                &nbsp;&nbsp;&nbsp;→ Ein Hit: 100.000+ Damage<br>
                &nbsp;&nbsp;&nbsp;→ <strong>Komplett nutzlos in hohen GRs!</strong>
            </div>
        </div>

        <div class="section">
            <h2>🔄 Beispiele: Was rerolled wenn beide da sind?</h2>
            <div class="info-box">
                <strong>Hast: Dex, Vit, Life Regen, LpH</strong><br>
                → Life Regen rerolled (schlechtester Stat)<br><br>

                <strong>Hast: Dex, Vit, Life Regen, Armor</strong><br>
                → Life Regen rerolled<br><br>

                <strong>Hast: Dex, LpH, Life Regen, Armor</strong><br>
                → Life Regen zu Vit rerolled (Vit > LpH)<br><br>

                <strong>Hast: Dex, Vit, Poison Res, Armor</strong><br>
                → Poison Res zu "Resistance to All Elements" rerolled<br><br>

                <strong>Hast: Dex, Vit, All Res, Life Regen</strong><br>
                → Life Regen zu Armor oder Life% rerolled
            </div>
            <p class="note">💡 Merke: Life Regen ist IMMER der erste Kandidat zum Rerolled!</p>
        </div>

        <div class="section">
            <h2>🎯 Was sollte ich rerolled?</h2>
            <div class="info-box">
                <strong>Jewelry (Ring/Amulet) - Socket fehlt:</strong><br>
                → Immer zuerst Socket rerolled!<br>
                → Ohne Socket kein Legendary Gem!<br><br>
                <strong>Waffen - Socket fehlt:</strong><br>
                → NICHT rerolled! Ramaladni's Gift nutzen!<br>
                → Gift gibt gratis Socket<br><br>
                <strong>Fehlender Offensive Stat:</strong><br>
                → CHC, CHD, CDR, Elemental% rerolled<br><br>
                <strong>Falscher Mainstat:</strong><br>
                → Int auf Monk Item → zu Dex rerolled<br><br>
                <strong>Unnützer Stat:</strong><br>
                → Life Regen, Thorns, Gold Find → weg damit
            </div>
        </div>

        <div class="section">
            <h2>💡 Enchanting pro Slot (Sunwuko Monk)</h2>
        </div>

        <div class="section">
            <h2>⚔️ Waffen (Won Khim Lau / Vengeful Wind)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> High Damage, Dex, Socket, +Damage%, Area Damage<br><br>
                <strong>Beispiel - WKL hat:</strong> 2800 DPS, Dex, Vit, Life per Hit<br>
                <strong>Problem:</strong> Vit und LpH sind nutzlos auf Waffe!<br><br>
                <strong>Lösung:</strong><br>
                1. Socket mit <strong>Ramaladni's Gift</strong> hinzufügen (NICHT rerolled!)<br>
                2. Vit → <strong>+10% Damage</strong> rerolled<br>
                → LpH bleibt leider (nur 1 Stat änderbar)<br><br>
                <strong>⚠️ NIEMALS rerolled:</strong><br>
                → Damage Range (die Würfelzahlen oben)<br>
                → Das ist der wichtigste Stat!
            </div>
        </div>

        <div class="section">
            <h2>👑 Helm (Sunwuko's Crown)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, Socket, CHC 6%, Tempest Rush %<br><br>
                <strong>Beispiel hat:</strong> Dex, Socket, Vit, All Res<br>
                <strong>Problem:</strong> Kein CHC, kein TR%!<br><br>
                <strong>Lösung:</strong> All Res → <strong>CHC 6%</strong> rerolled<br>
                → Vit ist okay für Toughness<br>
                → TR% wäre nice aber CHC ist wichtiger<br><br>
                <strong>Topaz im Socket:</strong> +12.5% RCR (Resource Cost Reduction)
            </div>
        </div>

        <div class="section">
            <h2>🦺 Chest (Sunwuko's Soul)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, Vit, 3 Sockets, Elite DR oder All Res<br><br>
                <strong>Beispiel hat:</strong> Dex, Vit, 3 Sockets, Life Regen<br>
                <strong>Problem:</strong> Life Regen ist fast nutzlos!<br><br>
                <strong>Lösung:</strong> Life Regen → <strong>All Res</strong> oder <strong>Elite Damage Reduction</strong><br>
                → Beides gut für Toughness<br>
                → Elite DR besser für GR Push
            </div>
        </div>

        <div class="section">
            <h2>💪 Shoulders (Mantle of Channeling)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, RCR 8%, CDR 8%, Area Damage 24%<br><br>
                <strong>Beispiel hat:</strong> Dex, Vit, All Res, Life%<br>
                <strong>Problem:</strong> Keine offensiven Stats!<br><br>
                <strong>Lösung:</strong> Life% → <strong>RCR 8%</strong> rerolled<br>
                → RCR wichtig für Tempest Rush Uptime<br>
                → Vit + All Res = gute Defense, behalten
            </div>
        </div>

        <div class="section">
            <h2>🧤 Gloves (Sunwuko's Paws)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, CHC 10%, CHD 50%, RCR 8% oder AD<br><br>
                <strong>Beispiel hat:</strong> Dex, CHC, Attack Speed, Vit<br>
                <strong>Problem:</strong> AS ist okay, Vit verschwendet<br><br>
                <strong>Lösung:</strong> Vit → <strong>CHD 50%</strong> rerolled<br>
                → CHC + CHD zusammen = beste Combo<br>
                → AS behalten (nicht schlecht für TR)
            </div>
        </div>

        <div class="section">
            <h2>🔮 Bracers (Cesar's Memento)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Cold% 20%, CHC 6%, Dex, LpH oder Vit<br><br>
                <strong>Beispiel hat:</strong> Dex, CHC, Vit, Thorns<br>
                <strong>Problem:</strong> Kein Cold%! Thorns nutzlos!<br><br>
                <strong>Lösung:</strong> Thorns → <strong>Cold Damage 20%</strong> rerolled<br>
                → Cold% ist RIESIGER Damage Boost!<br>
                → Multipliziert mit allem anderen<br><br>
                <strong>⚠️ Element MUSS zum Build passen!</strong><br>
                → Sunwuko TR = Cold (Flurry Rune)
            </div>
        </div>

        <div class="section">
            <h2>👖 Pants (Sunwuko's Leggings)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, Vit, 2 Sockets, Armor oder All Res<br><br>
                <strong>Beispiel hat:</strong> Dex, Vit, 2 Sockets, Life Regen<br>
                <strong>Problem:</strong> Life Regen wieder nutzlos<br><br>
                <strong>Lösung:</strong> Life Regen → <strong>Armor</strong> oder <strong>All Res</strong><br>
                → Hosen sind rein defensiv<br>
                → Keine offensiven Stats möglich hier
            </div>
        </div>

        <div class="section">
            <h2>👢 Boots (Captain Crimson's Waders)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, Vit, All Res, Tempest Rush 15%<br><br>
                <strong>Beispiel hat:</strong> Dex, Vit, Armor, Movement Speed<br>
                <strong>Problem:</strong> MS kommt von Paragon! Verschwendet!<br><br>
                <strong>Lösung:</strong> Movement Speed → <strong>Tempest Rush %</strong> rerolled<br>
                → TR% ist 15% MEHR DAMAGE!<br>
                → MS aus Paragon holen (gratis)
            </div>
            <p class="note">💡 Merke: Movement Speed NIE auf Gear wenn Paragon hoch genug!</p>
        </div>

        <div class="section">
            <h2>🎀 Belt (Captain Crimson's Silk Girdle)</h2>
            <div class="info-box">
                <strong>Perfekte Stats:</strong> Dex, Vit, All Res, Life%<br><br>
                <strong>Beispiel hat:</strong> Dex, Vit, Armor, Gold Find<br>
                <strong>Problem:</strong> Gold Find komplett nutzlos!<br><br>
                <strong>Lösung:</strong> Gold Find → <strong>All Res</strong> oder <strong>Life%</strong><br>
                → Belt ist rein defensiv<br>
                → Keine offensiven Stats möglich
            </div>
        </div>

        <div class="section">
            <h2>2. Reforging (Cube)</h2>
            <div class="info-box">
                <strong>Was ist das?</strong><br>
                Du würfelst ein Legendary Item KOMPLETT neu.<br>
                Alle Stats werden zufällig neu generiert.<br>
                Das Item kann dabei Ancient oder sogar Primal werden!
            </div>
        </div>

        <div class="section">
            <h2>📋 Reforging Schritt-für-Schritt</h2>
            <div class="info-box">
                <strong>Schritt 1:</strong> Bounties farmen (alle 5 Acts)<br>
                → Brauchst: 5x JEDES Bounty Material<br><br>
                <strong>Schritt 2:</strong> Forgotten Souls farmen<br>
                → Brauchst: 50 Forgotten Souls<br>
                → (Legendaries salvagen)<br><br>
                <strong>Schritt 3:</strong> Kanai's Cube → "Law of Kulle"<br><br>
                <strong>Schritt 4:</strong> Item + Mats reinlegen<br><br>
                <strong>Schritt 5:</strong> Transmute<br>
                → 10% Chance auf Ancient<br>
                → 0.25% Chance auf Primal
            </div>
        </div>

        <div class="section">
            <h2>🎯 Wann Reforgen?</h2>
            <div class="info-box">
                <strong>REFORGE wenn:</strong><br>
                • Du ein wichtiges Item hast aber es ist nicht Ancient<br>
                • Das Item ist Ancient aber Stats sind Müll<br>
                • Du ein Primal willst (viel Glück!)<br><br>
                <strong>NICHT REFORGE wenn:</strong><br>
                • Das Item hat bereits gute Stats<br>
                • Du wenig Bounty Mats hast<br>
                • Das Item ist leicht zu farmen (→ lieber neu droppen)
            </div>
        </div>

        <div class="section">
            <h2>💡 Reforge Beispiel (Monk Weapon)</h2>
            <div class="info-box">
                <strong>Situation:</strong> Won Khim Lau ist nicht Ancient<br>
                <strong>Problem:</strong> Waffen-Damage ist wichtigster Stat<br>
                → Ancient Weapon = ~15-20% mehr Damage!<br><br>
                <strong>Lösung:</strong> WKL immer wieder reforgen<br>
                → Bis Ancient mit gutem Damage Roll<br><br>
                <strong>Kosten pro Versuch:</strong><br>
                → 5x jedes Bounty Mat + 50 FS<br>
                → ~10 Versuche für Ancient (im Schnitt)
            </div>
            <p class="note">💡 Waffen haben höchste Reforge-Priorität wegen Damage!</p>
        </div>

        <div class="section">
            <h2>3. Augmenting (Caldesann's Despair)</h2>
            <div class="info-box">
                <strong>Was ist das?</strong><br>
                Du "opferst" einen hochgelevelten Legendary Gem um einem Ancient Item<br>
                permanent extra Mainstat zu geben. Der Gem wird dabei zerstört!
            </div>
        </div>

        <div class="section">
            <h2>📋 Augment Schritt-für-Schritt</h2>
            <div class="info-box">
                <strong>Schritt 1:</strong> Legendary Gem hochleveln<br>
                → GRs farmen, nach jedem GR Gem upgraden<br>
                → Ziel: mindestens Rank 50-100<br><br>
                <strong>Schritt 2:</strong> Ancient Item besorgen<br>
                → Nur ANCIENT (orange Rand) oder PRIMAL (rot) funktioniert!<br>
                → Normale Legendaries können NICHT augmentiert werden<br><br>
                <strong>Schritt 3:</strong> Kanai's Cube öffnen<br>
                → Letztes Rezept: "Caldesann's Despair"<br><br>
                <strong>Schritt 4:</strong> Items in den Cube legen<br>
                → Das Ancient Item<br>
                → Den Legendary Gem (wird zerstört!)<br>
                → 3x Flawless Royal Gem (passend zum Mainstat)<br><br>
                <strong>Schritt 5:</strong> Transmute drücken<br>
                → Item bekommt permanent +5 Mainstat pro Gem Level
            </div>
        </div>

        <div class="section">
            <h2>💎 Welchen Gem für welche Klasse?</h2>
            <div class="info-box">
                <strong style="color:#4ade80">Emerald (Grün)</strong> → Dexterity → Monk, Demon Hunter<br>
                <strong style="color:#ef4444">Ruby (Rot)</strong> → Strength → Barbarian, Crusader<br>
                <strong style="color:#facc15">Topaz (Gelb)</strong> → Intelligence → Wizard, WD, Necro<br>
                <strong style="color:#a78bfa">Amethyst (Lila)</strong> → Vitality → Alle (für Toughness)
            </div>
        </div>

        <div class="section">
            <h2>🔢 Beispielrechnung (Monk)</h2>
            <div class="info-box">
                <strong>Gem Rank 100 + Ancient Helm:</strong><br>
                → 100 × 5 = <strong>+500 Dexterity</strong> permanent auf dem Helm!<br><br>
                <strong>Alle 13 Slots mit Rank 100:</strong><br>
                → 13 × 500 = <strong>+6500 Dexterity</strong> extra!<br><br>
                <strong>Das entspricht ~650 Paragon Levels!</strong>
            </div>
            <p class="note">💡 Deshalb sind Augments so wichtig fürs Endgame</p>
        </div>

        <div class="section">
            <h2>⚠️ Augment Regeln</h2>
            <div class="info-box">
                • <strong>Nur Ancient/Primal</strong> - normale Legendaries gehen nicht!<br>
                • <strong>Gem wird zerstört</strong> - weg ist weg!<br>
                • <strong>Überschreibbar</strong> - neuer Augment ersetzt alten<br>
                • <strong>Minimum Gem Level:</strong><br>
                &nbsp;&nbsp;→ Waffen: Rank 30<br>
                &nbsp;&nbsp;→ Jewelry: Rank 40<br>
                &nbsp;&nbsp;→ Armor: Rank 50
            </div>
            <p class="note">Tipp: Erst augmenten wenn Item wirklich gut ist! Sonst Gem verschwendet.</p>
        </div>

        <div class="section">
            <h2>✅ Augment Tracker</h2>
            <div class="item"><input type="checkbox" id="aug1"><label for="aug1">Weapon augmentiert (Rank 100+ = +500 Dex)</label></div>
            <div class="item"><input type="checkbox" id="aug2"><label for="aug2">Helm augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug3"><label for="aug3">Chest augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug4"><label for="aug4">Pants augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug5"><label for="aug5">Boots augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug6"><label for="aug6">Gloves augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug7"><label for="aug7">Shoulders augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug8"><label for="aug8">Bracers augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug9"><label for="aug9">Belt augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug10"><label for="aug10">Amulet augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug11"><label for="aug11">Ring 1 augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug12"><label for="aug12">Ring 2 augmentiert</label></div>
            <div class="item"><input type="checkbox" id="aug13"><label for="aug13">Offhand augmentiert</label></div>
            <p class="note">💡 13 Slots × Rank 100 Gem = +6500 Mainstat!</p>
        </div>

        <div class="section">
            <h2>4. Ancient vs Primal</h2>
            <div class="info-box">
                <strong style="color:#f4a460">Ancient (Orange Rand):</strong><br>
                • ~10% höhere Stat Rolls als normal<br>
                • 10% Drop-Chance bei jeder Legendary<br>
                • Kann augmentiert werden<br><br>
                <strong style="color:#ef4444">Primal (Roter Rand + Pentagram):</strong><br>
                • PERFEKTE max Rolls auf allen Stats<br>
                • Nur ~0.25% Chance (1 von 400 Legendaries!)<br>
                • Kann augmentiert werden
            </div>
            <p class="note">⚠️ Wichtig: Schlechtes Ancient mit falschen Stats < Gutes Normal mit richtigen Stats!</p>
        </div>

        <div class="section">
            <h2>🔓 Primals freischalten</h2>
            <div class="info-box">
                <strong>Requirement:</strong> Solo GR70 abschließen!<br><br>
                • Muss SOLO sein (keine Gruppe)<br>
                • Einmal pro Season/Modus nötig<br>
                • Danach droppen Primals überall<br>
                • Erster Primal ist GARANTIERT nach GR70!
            </div>
            <div class="item"><input type="checkbox" id="gr70"><label for="gr70"><strong>Solo GR70 geschafft</strong> → Primals freigeschaltet!</label></div>
        </div>

        <div class="section">
            <h2>🎯 Primals "farmen"</h2>
            <div class="info-box">
                <strong>Schlechte Nachricht:</strong> Keine gezielte Farm möglich!<br>
                <strong>Gute Nachricht:</strong> Mehr Legendaries = Mehr Chancen<br><br>
                <strong>Beste Methoden:</strong><br>
                1. <strong>Speed GRs (85-95)</strong> in unter 5 Min<br>
                &nbsp;&nbsp;&nbsp;→ Meiste Legendaries pro Stunde<br><br>
                2. <strong>Kadala Gambling</strong><br>
                &nbsp;&nbsp;&nbsp;→ Kann Primal droppen!<br><br>
                3. <strong>Cube Upgrade Rare</strong><br>
                &nbsp;&nbsp;&nbsp;→ Kann Primal werden!<br><br>
                4. <strong>Cube Reforge</strong><br>
                &nbsp;&nbsp;&nbsp;→ 0.25% Chance auf Primal
            </div>
            <p class="note">📊 Statistik: ~2 Stunden Speed GR60 = 1 Primal (im Durchschnitt)</p>
        </div>

        <div class="section">
            <h2>🔍 Gear Checker - Was soll ich rerolled?</h2>
            <p class="note">Wähle welche Stats dein Item HAT, dann siehst du was du rerolled sollst!</p>
        </div>

        <div class="section gear-checker">
            <h2>⚔️ Mainhand (Won Khim Lau)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="mh" data-stat="socket"> Socket</label>
                <label><input type="checkbox" data-slot="mh" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="mh" data-stat="dmgpct"> +% Damage</label>
                <label><input type="checkbox" data-slot="mh" data-stat="ad"> Area Damage</label>
                <label><input type="checkbox" data-slot="mh" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="mh" data-stat="lph"> Life per Hit</label>
                <label><input type="checkbox" data-slot="mh" data-stat="cdr"> CDR</label>
                <label><input type="checkbox" data-slot="mh" data-stat="rcr"> RCR</label>
            </div>
            <div class="reroll-advice" id="advice-mh">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>⚔️ Offhand (Vengeful Wind)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="oh" data-stat="socket"> Socket</label>
                <label><input type="checkbox" data-slot="oh" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="oh" data-stat="dmgpct"> +% Damage</label>
                <label><input type="checkbox" data-slot="oh" data-stat="ad"> Area Damage</label>
                <label><input type="checkbox" data-slot="oh" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="oh" data-stat="lph"> Life per Hit</label>
                <label><input type="checkbox" data-slot="oh" data-stat="cdr"> CDR</label>
                <label><input type="checkbox" data-slot="oh" data-stat="rcr"> RCR</label>
            </div>
            <div class="reroll-advice" id="advice-oh">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>👑 Helm (Sunwuko's Crown)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="helm" data-stat="socket"> Socket</label>
                <label><input type="checkbox" data-slot="helm" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="helm" data-stat="chc"> CHC 6%</label>
                <label><input type="checkbox" data-slot="helm" data-stat="skill"> TR% oder Skill%</label>
                <label><input type="checkbox" data-slot="helm" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="helm" data-stat="allres"> All Res</label>
            </div>
            <div class="reroll-advice" id="advice-helm">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>💪 Shoulders (Mantle of Channeling)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="shoulders" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="shoulders" data-stat="rcr"> RCR 8%</label>
                <label><input type="checkbox" data-slot="shoulders" data-stat="cdr"> CDR 8%</label>
                <label><input type="checkbox" data-slot="shoulders" data-stat="ad"> Area Damage</label>
                <label><input type="checkbox" data-slot="shoulders" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="shoulders" data-stat="allres"> All Res</label>
                <label><input type="checkbox" data-slot="shoulders" data-stat="life"> Life%</label>
            </div>
            <div class="reroll-advice" id="advice-shoulders">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>🦺 Chest (Sunwuko's Soul)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="chest" data-stat="sockets"> 3 Sockets</label>
                <label><input type="checkbox" data-slot="chest" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="chest" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="chest" data-stat="allres"> All Res</label>
                <label><input type="checkbox" data-slot="chest" data-stat="elite"> Elite DR%</label>
                <label><input type="checkbox" data-slot="chest" data-stat="armor"> Armor</label>
                <label><input type="checkbox" data-slot="chest" data-stat="life"> Life%</label>
            </div>
            <div class="reroll-advice" id="advice-chest">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>🧤 Gloves (Sunwuko's Paws)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="gloves" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="gloves" data-stat="chc"> CHC 10%</label>
                <label><input type="checkbox" data-slot="gloves" data-stat="chd"> CHD 50%</label>
                <label><input type="checkbox" data-slot="gloves" data-stat="rcr"> RCR 8%</label>
                <label><input type="checkbox" data-slot="gloves" data-stat="ad"> Area Damage</label>
                <label><input type="checkbox" data-slot="gloves" data-stat="as"> Attack Speed</label>
                <label><input type="checkbox" data-slot="gloves" data-stat="vit"> Vit</label>
            </div>
            <div class="reroll-advice" id="advice-gloves">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>🔮 Bracers (Cesar's Memento)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="bracers" data-stat="ele"> Cold% 20%</label>
                <label><input type="checkbox" data-slot="bracers" data-stat="chc"> CHC 6%</label>
                <label><input type="checkbox" data-slot="bracers" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="bracers" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="bracers" data-stat="lph"> Life per Hit</label>
                <label><input type="checkbox" data-slot="bracers" data-stat="allres"> All Res</label>
                <label><input type="checkbox" data-slot="bracers" data-stat="armor"> Armor</label>
            </div>
            <div class="reroll-advice" id="advice-bracers">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>🎀 Belt (Captain Crimson's Silk Girdle)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="belt" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="belt" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="belt" data-stat="allres"> All Res</label>
                <label><input type="checkbox" data-slot="belt" data-stat="life"> Life%</label>
                <label><input type="checkbox" data-slot="belt" data-stat="armor"> Armor</label>
            </div>
            <div class="reroll-advice" id="advice-belt">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>👖 Pants (Sunwuko's Leggings)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="pants" data-stat="sockets"> 2 Sockets</label>
                <label><input type="checkbox" data-slot="pants" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="pants" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="pants" data-stat="allres"> All Res</label>
                <label><input type="checkbox" data-slot="pants" data-stat="armor"> Armor</label>
            </div>
            <div class="reroll-advice" id="advice-pants">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>👢 Boots (Captain Crimson's Waders)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="boots" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="boots" data-stat="vit"> Vit</label>
                <label><input type="checkbox" data-slot="boots" data-stat="skill"> TR% 15%</label>
                <label><input type="checkbox" data-slot="boots" data-stat="allres"> All Res</label>
                <label><input type="checkbox" data-slot="boots" data-stat="armor"> Armor</label>
                <label><input type="checkbox" data-slot="boots" data-stat="ms"> Movement Speed</label>
            </div>
            <div class="reroll-advice" id="advice-boots">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>💍 Ring 1 (Ring of Royal Grandeur)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="ring1" data-stat="socket"> Socket</label>
                <label><input type="checkbox" data-slot="ring1" data-stat="chc"> CHC</label>
                <label><input type="checkbox" data-slot="ring1" data-stat="chd"> CHD</label>
                <label><input type="checkbox" data-slot="ring1" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="ring1" data-stat="ad"> Area Damage</label>
                <label><input type="checkbox" data-slot="ring1" data-stat="as"> Attack Speed</label>
                <label><input type="checkbox" data-slot="ring1" data-stat="rcr"> RCR</label>
            </div>
            <div class="reroll-advice" id="advice-ring1">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>💍 Ring 2 (Obsidian Ring / CoE)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="ring2" data-stat="socket"> Socket</label>
                <label><input type="checkbox" data-slot="ring2" data-stat="chc"> CHC</label>
                <label><input type="checkbox" data-slot="ring2" data-stat="chd"> CHD</label>
                <label><input type="checkbox" data-slot="ring2" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="ring2" data-stat="ad"> Area Damage</label>
                <label><input type="checkbox" data-slot="ring2" data-stat="as"> Attack Speed</label>
                <label><input type="checkbox" data-slot="ring2" data-stat="rcr"> RCR</label>
            </div>
            <div class="reroll-advice" id="advice-ring2">Wähle deine Stats...</div>
        </div>

        <div class="section gear-checker">
            <h2>📿 Amulet (Squirt's / Flavor of Time)</h2>
            <div class="stat-checks">
                <label><input type="checkbox" data-slot="amulet" data-stat="socket"> Socket</label>
                <label><input type="checkbox" data-slot="amulet" data-stat="ele"> Cold% 20%</label>
                <label><input type="checkbox" data-slot="amulet" data-stat="chc"> CHC 10%</label>
                <label><input type="checkbox" data-slot="amulet" data-stat="chd"> CHD 100%</label>
                <label><input type="checkbox" data-slot="amulet" data-stat="dex"> Dex</label>
                <label><input type="checkbox" data-slot="amulet" data-stat="rcr"> RCR</label>
            </div>
            <div class="reroll-advice" id="advice-amulet">Wähle deine Stats...</div>
        </div>

        <div class="section">
            <h2>♻️ Primal salvagen = Primordial Ashes</h2>
            <div class="info-box">
                <strong>Primal Item salvagen:</strong> Gibt 55 Primordial Ashes<br>
                <strong>Nutzen:</strong> Altar Potion Powers freischalten<br><br>
                → Salvage unnütze Primals (falsche Klasse/Build)<br>
                → Behalte nur Primals die du wirklich nutzt
            </div>
        </div>

        <div class="section">
            <h2>✅ Ancient Checklist</h2>
            <div class="item"><input type="checkbox" id="anc1"><label for="anc1">Mainhand Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc2"><label for="anc2">Offhand Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc3"><label for="anc3">Helm Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc4"><label for="anc4">Chest Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc5"><label for="anc5">Shoulders Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc6"><label for="anc6">Gloves Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc7"><label for="anc7">Bracers Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc8"><label for="anc8">Belt Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc9"><label for="anc9">Pants Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc10"><label for="anc10">Boots Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc11"><label for="anc11">Amulet Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc12"><label for="anc12">Ring 1 Ancient</label></div>
            <div class="item"><input type="checkbox" id="anc13"><label for="anc13">Ring 2 Ancient</label></div>
        </div>'''


def _generate_bosses_html(static: dict) -> str:
    """Generate the Bosses tab HTML with search."""
    bosses = static.get('bosses', {}).get('story_bosses', {})
    keywardens = static.get('keywardens', {})

    boss_cards = ''

    # Story Bosses
    for boss_id, boss in sorted(bosses.items(), key=lambda x: (x[1].get('act', 0), x[1].get('name', ''))):
        name = boss.get('name', boss_id)
        name_de = boss.get('name_de', '')
        act = boss.get('act', '?')
        location = boss.get('location', '?')
        waypoint = boss.get('waypoint', '')
        notes = boss.get('notes', '')

        name_display = f"{name} ({name_de})" if name_de else name
        notes_html = f'<div class="notes">{notes}</div>' if notes else ''

        boss_cards += f'''            <div class="boss-card" data-type="boss">
                <h4>{name_display} <span class="act-badge">Act {act}</span></h4>
                <div class="location">{location}</div>
                <div class="waypoint">WP: {waypoint}</div>
                {notes_html}
            </div>\n'''

    # Keywardens section
    boss_cards += '''            <div class="section" style="margin-top: 15px; padding: 0;">
                <h2 style="padding: 12px 12px 8px 12px;">Keywardens</h2>
            </div>\n'''

    for kw_id, kw in sorted(keywardens.items(), key=lambda x: x[1].get('act', 0)):
        name = kw.get('name', kw_id)
        act = kw.get('act', '?')
        location = kw.get('location', '?')
        drops = kw.get('drops', '')

        boss_cards += f'''            <div class="boss-card" data-type="keywarden">
                <h4>{name} <span class="act-badge">Act {act}</span></h4>
                <div class="location">{location}</div>
                <div class="waypoint">Drops: {drops}</div>
            </div>\n'''

    return f'''        <div class="section">
            <h2>Boss & Keywarden Suche</h2>
            <input type="text" id="bossSearch" class="search-box" placeholder="Boss suchen... (z.B. Belial, Act 3, Oasis)">
        </div>
{boss_cards}'''


def _generate_altar_html(static: dict) -> str:
    """Generate the Altar tab HTML."""
    altar = static.get('altar_of_rites', {})
    unlock_order = altar.get('unlock_order', [])
    potions = altar.get('potion_powers', {})

    # Seal list with costs as checkboxes
    seal_items = ''
    for seal in unlock_order:
        num = seal.get('seal', '?')
        name = seal.get('name', '?')
        effect = seal.get('effect', '')
        cost = seal.get('cost', '?')
        warning = seal.get('warning', '')

        warning_html = f' <span style="color:#e94560">⚠️ {warning}</span>' if warning else ''

        seal_items += f'''            <div class="item">
                <input type="checkbox" id="altar_{num}">
                <label for="altar_{num}">
                    <strong style="color:#f4a460">{num}. {name}</strong><br>
                    <span style="font-size:0.85em">{effect}</span><br>
                    <span class="diff">Kosten: {cost}</span>{warning_html}
                </label>
            </div>\n'''

    return f'''        <div class="section">
            <h2>Altar of Rites</h2>
            <p class="note">📍 Act I, New Tristram - links vom Waypoint</p>
            <div class="info-box">
                26 Seals + 3 Potion Powers | Alle Powers permanent für Season
            </div>
        </div>

        <div class="section">
            <h2>Alle 26 Seals (mit Kosten)</h2>
{seal_items}        </div>

        <div class="section">
            <h2>🧪 Potion Powers</h2>
            <div class="info-box">
                <strong>AA (55 Ashes):</strong> Runic circles - Dmg/CDR/RCR<br>
                <strong>AB (110 Ashes):</strong> Enemies deal 25% less damage<br>
                <strong>AC (165 Ashes):</strong> Random shrine effect<br>
                <strong>AD (Auto nach 26 Seals):</strong> Double Primal drops
            </div>
            <p class="note">Primordial Ashes = Primal Items salvagen</p>
        </div>'''


def _generate_start_html(start_guide: dict) -> str:
    """Generate the Season Start tab HTML."""
    if not start_guide:
        return '<div class="section"><h2>Season Start</h2><p>Keine Daten.</p></div>'

    # Challenge Rift Cache Info
    prep = start_guide.get('preparation', {})
    cr = prep.get('challenge_rift', {})
    cache = cr.get('cache_contents', {})

    # Season Start Steps
    steps = start_guide.get('season_start_steps', {})

    # Phase 1: Nach Login
    phase1 = steps.get('phase_1', {})
    phase1_items = ''
    for i, step in enumerate(phase1.get('steps', []), 1):
        action = step.get('action', '')
        notes = step.get('notes', '')
        notes_html = f'<span class="diff">{notes}</span>' if notes else ''
        phase1_items += f'            <div class="item"><input type="checkbox" id="start_p1_{i}"><label for="start_p1_{i}">{action} {notes_html}</label></div>\n'

    # Phase 2: Altar
    phase2 = steps.get('phase_2', {})
    phase2_items = ''
    for i, step in enumerate(phase2.get('steps', []), 1):
        action = step.get('action', '')
        effect = step.get('effect', '')
        cost = step.get('cost', '')
        notes_html = f'<span class="diff">({cost})</span>' if cost else ''
        phase2_items += f'            <div class="item"><input type="checkbox" id="start_p2_{i}"><label for="start_p2_{i}">{action} {notes_html}</label></div>\n'
        if effect:
            phase2_items += f'            <p class="note">{effect}</p>\n'

    # Phase 3: Gear craften
    phase3 = steps.get('phase_3', {})
    phase3_items = ''
    for i, step in enumerate(phase3.get('steps', []), 1):
        action = step.get('action', '')
        notes = step.get('notes', '')
        notes_html = f'<span class="diff">{notes}</span>' if notes else ''
        phase3_items += f'            <div class="item"><input type="checkbox" id="start_p3_{i}"><label for="start_p3_{i}">{action} {notes_html}</label></div>\n'

    # Phase 4: Cube
    phase4 = steps.get('phase_4', {})
    phase4_items = ''
    for i, step in enumerate(phase4.get('steps', []), 1):
        action = step.get('action', '')
        location = step.get('location', '')
        notes_html = f'<span class="diff">{location}</span>' if location else ''
        phase4_items += f'            <div class="item"><input type="checkbox" id="start_p4_{i}"><label for="start_p4_{i}">{action} {notes_html}</label></div>\n'

    # Phase 5: Leveling
    phase5 = steps.get('phase_5', {})
    gambling = phase5.get('gambling_priority', {}).get('level_1', [])
    gambling_items = ''
    for g in gambling:
        slot = g.get('slot', '')
        target = g.get('target', '')
        effect = g.get('effect', '')
        gambling_items += f'            <div class="item"><input type="checkbox" id="start_gamble_{slot}"><label for="start_gamble_{slot}"><strong>{slot}</strong> → {target}</label></div>\n'
        if effect:
            gambling_items += f'            <p class="note">{effect}</p>\n'

    # Common mistakes
    mistakes = start_guide.get('common_mistakes', [])
    mistakes_html = ''
    for m in mistakes[:5]:  # Top 5 mistakes
        mistake = m.get('mistake', '')
        fix = m.get('fix', '')
        mistakes_html += f'<strong>❌ {mistake}</strong><br>✅ {fix}<br><br>\n'

    # Timeline
    timeline = start_guide.get('timeline', {}).get('solo', {})
    timeline_html = ''
    for time, activity in timeline.items():
        timeline_html += f'<strong>{time}</strong> - {activity}<br>\n'

    return f'''        <div class="section">
            <h2>Challenge Rift Cache</h2>
            <div class="info-box">
                <strong>Inhalt:</strong><br>
                💰 {cache.get('gold', '5.1M')} Gold<br>
                🩸 {cache.get('blood_shards', 475)} Blood Shards<br>
                💀 {cache.get('deaths_breath', 35)} Death's Breath<br>
                📦 {cache.get('reusable_parts', 300)} Reusable Parts + Arcane Dust + Veiled Crystal<br>
                🗺️ 15x Bounty Mats (jeder Act)
            </div>
            <p class="note">⚠️ WICHTIG: Erst NACH Season-Start öffnen! Vorher Season-Char erstellen!</p>
        </div>

        <div class="section">
            <h2>Phase 1: Nach Login</h2>
{phase1_items}        </div>

        <div class="section">
            <h2>Phase 2: Altar of Rites</h2>
            <p class="note">📍 Act 1, New Tristram - links vom Waypoint</p>
{phase2_items}        </div>

        <div class="section">
            <h2>Phase 3: Level 70 Gear craften</h2>
            <p class="note">⚠️ Braucht Anointed Seal!</p>
{phase3_items}        </div>

        <div class="section">
            <h2>Phase 4: Kanai's Cube</h2>
            <p class="note">📍 Act 3, Ruins of Sescheron → Elder Sanctum</p>
{phase4_items}        </div>

        <div class="section">
            <h2>Phase 5: Necro Gambling (Level 1)</h2>
            <p class="note">Necro hat die besten Level-1-Gambling Optionen!</p>
{gambling_items}        </div>

        <div class="section">
            <h2>⏱️ Zeitleiste (Solo)</h2>
            <div class="info-box">
{timeline_html}            </div>
        </div>

        <div class="section">
            <h2>⚠️ Häufige Fehler</h2>
            <div class="info-box">
{mistakes_html}            </div>
        </div>'''


def _generate_glossary_html(glossary: dict) -> str:
    """Generate the Glossary tab HTML with search."""
    if not glossary:
        return '<div class="section"><h2>Glossar</h2><p>Keine Daten.</p></div>'

    # Collect all terms from all categories
    all_terms = []

    categories = {
        'stats': 'Stats & Attribute',
        'content': 'Game Content',
        'items': 'Items & Gear',
        'cube': 'Cube & Crafting',
        'gameplay': 'Gameplay',
        'classes': 'Klassen',
        'community': 'Community & Meta'
    }

    for cat_key, cat_name in categories.items():
        cat_data = glossary.get(cat_key, {})
        for abbr, data in cat_data.items():
            if isinstance(data, dict):
                all_terms.append({
                    'abbr': abbr,
                    'full': data.get('full', ''),
                    'deutsch': data.get('deutsch', ''),
                    'description': data.get('description', ''),
                    'notes': data.get('notes', ''),
                    'category': cat_name
                })

    # Sort by abbreviation
    all_terms.sort(key=lambda x: x['abbr'].lower())

    # Generate term cards
    term_cards = ''
    for term in all_terms:
        abbr = term['abbr']
        full = term['full']
        deutsch = term['deutsch']
        desc = term['description']
        notes = term['notes']
        cat = term['category']

        deutsch_html = f' / {deutsch}' if deutsch and deutsch != full else ''
        notes_html = f'<div class="notes" style="color:#888;font-size:0.8em;margin-top:3px">{notes}</div>' if notes else ''

        term_cards += f'''            <div class="boss-card glossary-term">
                <h4 style="color:#e94560">{abbr}</h4>
                <div style="color:#f4a460">{full}{deutsch_html}</div>
                <div style="color:#ccc;font-size:0.85em;margin-top:3px">{desc}</div>
                {notes_html}
                <div style="color:#666;font-size:0.7em;margin-top:5px">{cat}</div>
            </div>\n'''

    return f'''        <div class="section">
            <h2>Glossar / Abkürzungen</h2>
            <input type="text" id="glossarySearch" class="search-box" placeholder="Suchen... (z.B. CHC, CDR, GR, Primal)">
            <p class="note">{len(all_terms)} Einträge</p>
        </div>
{term_cards}
        <script>
            const glossarySearch = document.getElementById('glossarySearch');
            if (glossarySearch) {{
                glossarySearch.addEventListener('input', (e) => {{
                    const query = e.target.value.toLowerCase();
                    document.querySelectorAll('.glossary-term').forEach(card => {{
                        const text = card.textContent.toLowerCase();
                        card.classList.toggle('hidden', !text.includes(query));
                    }});
                }});
            }}
        </script>'''


def _generate_farm_html(static: dict, build: dict) -> str:
    """Generate the Farm tab HTML."""
    kadala = static.get('kadala', {})
    bounty = static.get('bounty_cache_items', {})
    difficulties = static.get('difficulties', {})

    # Bounty items
    bounty_items = ''
    for act_key in ['act_1', 'act_2', 'act_3']:
        act_num = act_key.split('_')[1]
        items = bounty.get(act_key, [])
        high_prio = [i for i in items if i.get('priority') == 'high']
        for item in high_prio:
            bounty_items += f'''            <div class="item"><input type="checkbox" id="bounty_{act_key}"><label for="bounty_{act_key}">Act {act_num} → {item.get('name', '?')}</label></div>\n'''

    # Difficulty drop rates table (alle Torment-Stufen)
    diff_order = ['torment_1', 'torment_2', 'torment_3', 'torment_4', 'torment_5', 'torment_6', 'torment_7', 'torment_8', 'torment_9', 'torment_10', 'torment_11', 'torment_12', 'torment_13', 'torment_14', 'torment_15', 'torment_16']
    diff_rows = ''
    for diff_key in diff_order:
        if diff_key in difficulties:
            d = difficulties[diff_key]
            name = d.get('name', diff_key)
            leg_bonus = d.get('legendary_bonus', 0)
            leg_rift = d.get('legendary_bonus_rift', 0)
            db_chance = d.get('deaths_breath_chance', '-')
            gr_eq = d.get('gr_equivalent', '-')
            diff_rows += f'<tr><td>{name}</td><td>+{leg_bonus}%</td><td>+{leg_rift}%</td><td>{db_chance}%</td><td>GR{gr_eq}</td></tr>\n'

    return f'''        <div class="section">
            <h2>🚀 Farming Grundregel</h2>
            <div class="info-box">
                <strong>SCHNELL > HOCH!</strong><br><br>
                ❌ GR70 in 6 Minuten = wenig Loot pro Stunde<br>
                ✅ GR55 in 2 Minuten = VIEL mehr Loot pro Stunde!<br><br>
                <strong>Ziel:</strong> Das höchste GR in 2-3 Minuten clearen
            </div>
            <p class="note">💡 Mehr Runs = Mehr Drops = Mehr Upgrades + Mehr Ramaladni Chancen!</p>
        </div>

        <div class="section">
            <h2>📊 Finde dein Speed-GR Level</h2>
            <div class="info-box">
                <strong>So findest du dein optimales Level:</strong><br><br>
                1. Starte bei GR55<br>
                2. War es unter 3 Min? → Das ist dein Farm-Level<br>
                3. Zu leicht? → GR60 probieren<br>
                4. Zu langsam? → GR50 probieren<br><br>
                <strong>Ziel-Zeit pro GR:</strong> 2-3 Minuten
            </div>
        </div>

        <div class="section">
            <h2>🎁 Ramaladni's Gift farmen</h2>
            <div class="info-box">
                <strong>Was ist das?</strong><br>
                Fügt einer Waffe einen GRATIS Socket hinzu!<br>
                Verbraucht keinen Reroll-Slot!<br><br>
                <strong>Wo droppt es?</strong><br>
                ✅ Greater Rifts (beste Methode!)<br>
                ✅ Nephalem Rifts<br>
                ✅ Überall als World Drop<br>
                ❌ NICHT gezielt farmbar<br><br>
                <strong>Wie bekomme ich es?</strong><br>
                → Mehr Legendaries sehen = Mehr Chancen<br>
                → Speed GRs/Rifts auf deinem schnellen Level<br>
                → Einfach spielen, es kommt irgendwann!
            </div>
            <p class="note">⚠️ Ramaladni's Gift ist selten! Nicht aufgeben, weiterspielen!</p>
        </div>

        <div class="section">
            <h2>📋 Aktivitäten - Wann was machen?</h2>
            <div class="info-box">
                <table style="width:100%; font-size:0.9em;">
                    <tr style="border-bottom:1px solid #444"><td><strong>Speed GRs</strong></td><td>Hauptaktivität! Loot, Gems leveln, Paragon, Keys</td></tr>
                    <tr style="border-bottom:1px solid #444"><td><strong>Nephalem Rifts</strong></td><td>GR Keys farmen, Death's Breath</td></tr>
                    <tr style="border-bottom:1px solid #444"><td><strong>Bounties</strong></td><td>Nur wenn du Reforge-Mats brauchst</td></tr>
                    <tr style="border-bottom:1px solid #444"><td><strong>Echoing Nightmare</strong></td><td>Augment-Gems (Whisper of Atonement)</td></tr>
                    <tr><td><strong>Uber Bosses</strong></td><td>Hellfire Amulet (optional)</td></tr>
                </table>
            </div>
        </div>

        <div class="section">
            <h2>🧱 Plateau durchbrechen</h2>
            <div class="info-box">
                <strong>Steckst du fest? Hier ist der Plan:</strong><br><br>
                1️⃣ <strong>Runter mit dem GR Level!</strong><br>
                &nbsp;&nbsp;&nbsp;→ Farm auf 2-3 Min Level, nicht am Limit<br><br>
                2️⃣ <strong>Legendary Gems leveln</strong><br>
                &nbsp;&nbsp;&nbsp;→ Bane of Trapped, Taeguk auf 80+<br>
                &nbsp;&nbsp;&nbsp;→ Oft mehr Damage als Gear-Upgrades!<br><br>
                3️⃣ <strong>Paragon sammeln</strong><br>
                &nbsp;&nbsp;&nbsp;→ Jeder Paragon = +5 Mainstat<br>
                &nbsp;&nbsp;&nbsp;→ Passiver, stetiger Power-Gewinn<br><br>
                4️⃣ <strong>Cube Reforge für Ancient</strong><br>
                &nbsp;&nbsp;&nbsp;→ Bounties für Mats<br>
                &nbsp;&nbsp;&nbsp;→ Schlechte Items reforgen<br>
                &nbsp;&nbsp;&nbsp;→ 10% Chance auf Ancient!<br><br>
                5️⃣ <strong>Augments starten</strong><br>
                &nbsp;&nbsp;&nbsp;→ Auch Level 80 Gems lohnen sich<br>
                &nbsp;&nbsp;&nbsp;→ +400 Dex × 13 Slots = +5200 Dex!
            </div>
        </div>

        <div class="section">
            <h2>⚡ Quick Farm Session (30 Min)</h2>
            <div class="info-box">
                <strong>Ziel:</strong> Maximaler Loot in kurzer Zeit<br><br>
                1. GR auf Speed-Level starten (2-3 Min)<br>
                2. 10-15 GRs durchrushen<br>
                3. Alle Legendaries mitnehmen<br>
                4. Am Ende: Gems upgraden<br>
                5. Schlechte Legs salvagen = Forgotten Souls<br><br>
                <strong>Ergebnis:</strong><br>
                • 50-100+ Legendaries gesehen<br>
                • Paragon XP<br>
                • Gem Level ups<br>
                • Chance auf Ramaladni's Gift<br>
                • Forgotten Souls für Reforge
            </div>
        </div>

        <div class="section">
            <h2>🎯 Was bringt am meisten Power?</h2>
            <div class="info-box">
                <strong>Ranking (von meiste zu wenigste Impact):</strong><br><br>
                1. <strong>Richtige Items + Set</strong> → Hast du ✅<br>
                2. <strong>Legendary Gems 80+</strong> → Riesiger Damage!<br>
                3. <strong>Ancient Weapons</strong> → 15-20% mehr Damage<br>
                4. <strong>Richtige Stats (CHC/CHD)</strong> → Enchanting<br>
                5. <strong>Augments</strong> → +5000 Mainstat möglich<br>
                6. <strong>Ancient Armor</strong> → Weniger Impact als Waffen<br>
                7. <strong>Paragon</strong> → Langsam aber stetig<br>
                8. <strong>Primal Items</strong> → Nice to have, nicht nötig
            </div>
        </div>

        <div class="section">
            <h2>Torment Drop Rates</h2>
            <table class="skill-table">
                <tr><th>Stufe</th><th>Leg%</th><th>Rift%</th><th>DB%</th><th>GR</th></tr>
{diff_rows}            </table>
            <p class="note">Leg% = Legendary Bonus (Open World), Rift% = in Nephalem Rifts, DB% = Death's Breath Chance</p>
        </div>

        <div class="section">
            <h2>🎰 Kadala Gambling Guide</h2>
            <div class="info-box">
                <strong>Kosten pro Slot:</strong><br>
                • <strong>25 Shards:</strong> Helm, Shoulders, Chest, Gloves, Belt, Pants, Boots, Bracers<br>
                • <strong>50 Shards:</strong> Rings<br>
                • <strong>75 Shards:</strong> 1H Weapons, Offhands, Shields<br>
                • <strong>100 Shards:</strong> Amulet, 2H Weapons
            </div>
        </div>

        <div class="section">
            <h2>✅ Bei Kadala gamblen (kleine Pools)</h2>
            <div class="info-box">
                <strong>Bracers - BESTE Kadala Slot!</strong><br>
                → Nur ~15 mögliche Legendaries<br>
                → Cesar's Memento relativ leicht zu bekommen<br>
                → Spirit Guards auch hier<br><br>

                <strong>Belt - Sehr guter Slot</strong><br>
                → Kleiner Pool ~20 Items<br>
                → Witching Hour, Kyoshiro's Soul, etc.<br><br>

                <strong>Helm - Okay</strong><br>
                → Sunwuko's Crown, Eye of Peshkov<br>
                → Mittlerer Pool<br><br>

                <strong>Gloves/Boots/Shoulders/Chest/Pants</strong><br>
                → Set-Teile hier gamblen<br>
                → Mittlerer Pool, okay Chancen
            </div>
        </div>

        <div class="section">
            <h2>❌ NICHT bei Kadala (große Pools / teuer)</h2>
            <div class="info-box">
                <strong>Waffen - NIEMALS bei Kadala!</strong><br>
                → Riesiger Loot Pool (100+ Legendaries!)<br>
                → 75 Shards pro Versuch<br>
                → Chance auf spezifische Waffe = winzig<br>
                → <strong>IMMER im Cube upgraden!</strong><br><br>

                <strong>Ringe - Nur wenn verzweifelt</strong><br>
                → 50 Shards, großer Pool<br>
                → Cube Upgrade ist besser<br><br>

                <strong>Amulet - Fast nie</strong><br>
                → 100 Shards pro Versuch!<br>
                → Riesiger Pool<br>
                → Cube Upgrade nutzen
            </div>
        </div>

        <div class="section">
            <h2>⚗️ Cube Upgrade statt Kadala</h2>
            <div class="info-box">
                <strong>Rezept:</strong> Rare (Yellow) + 25 DB + 50 jeder Mat<br>
                <strong>Ergebnis:</strong> Zufällige Legendary DERSELBEN Kategorie<br><br>

                <strong>Warum besser für Waffen?</strong><br>
                → 1H Fist Weapons = nur ~8 mögliche!<br>
                → Kadala 1H Weapons = 100+ möglich!<br>
                → Chance auf Won Khim Lau/Vengeful Wind viel höher!<br><br>

                <strong>So geht's:</strong><br>
                1. Rare Fist Weapon beim Blacksmith craften<br>
                2. Im Cube: "Upgrade Rare Item"<br>
                3. Wird zu random Legendary Fist Weapon<br>
                4. Wiederholen bis WKL/VW
            </div>
        </div>

        <div class="section">
            <h2>🎯 Sunwuko Monk - Wo was farmen?</h2>
            <div class="info-box">
                <strong>KADALA (gamblen):</strong><br>
                ✅ Bracers → Cesar's Memento, Spirit Guards<br>
                ✅ Belt → Kyoshiro's Soul<br>
                ✅ Helm → Sunwuko's Crown<br>
                ✅ Boots → Sunwuko's Shines, Crudest Boots<br>
                ✅ Shoulders → Sunwuko's Balance, Mantle of Channeling<br>
                ✅ Chest → Sunwuko's Soul<br>
                ✅ Gloves → Sunwuko's Paws<br>
                ✅ Pants → Sunwuko's Leggings<br><br>

                <strong>CUBE UPGRADE (nicht Kadala!):</strong><br>
                ⚗️ Fist Weapons → Won Khim Lau, Vengeful Wind<br>
                ⚗️ Rings → Ring of Royal Grandeur (oder A1 Bounty)<br>
                ⚗️ Amulet → Squirt's Necklace, Flavor of Time<br><br>

                <strong>BOUNTIES:</strong><br>
                🎁 Act 1 → Ring of Royal Grandeur<br>
                🎁 Act 2 → Gloves of Worship (Follower)<br>
                🎁 Act 3 → Avarice Band (Follower)<br><br>

                <strong>RANDOM DROP:</strong><br>
                💀 Balance Daibo → überall (World Drop)
            </div>
        </div>

        <div class="section">
            <h2>Bounty Cache Items</h2>
{bounty_items}        </div>

        <div class="section">
            <h2>Cube Upgrade (Rare → Legendary)</h2>
            <div class="info-box">
                25 Death's Breath + 50 jeder Mat-Art<br>
                <strong>Tipp:</strong> Weapons hier upgraden, nicht bei Kadala!
            </div>
        </div>

        <div class="section">
            <h2>🎲 Cube Portal Items</h2>
            <p class="note">Diese Items im Cube transmuten (ohne weitere Zutaten):</p>
            <div class="item"><input type="checkbox" id="cp1"><label for="cp1"><strong>Puzzle Ring</strong> → The Vault<br><span class="diff">Gold, Gems, Boon of the Hoarder von Greed</span></label></div>
            <div class="item"><input type="checkbox" id="cp2"><label for="cp2"><strong>Ancient Puzzle Ring</strong> → Ancient Vault<br><span class="diff">Viel mehr Gold/Gems/Goblins!</span></label></div>
            <div class="item"><input type="checkbox" id="cp3"><label for="cp3"><strong>Bovine Bardiche</strong> → Not The Cow Level<br><span class="diff">Chests, Shrines, Pools (1x pro Game!)</span></label></div>
            <div class="item"><input type="checkbox" id="cp4"><label for="cp4"><strong>Petrified Scream</strong> → Echoing Nightmare<br><span class="diff">Whisper of Atonement für Augments</span></label></div>
        </div>

        <div class="section">
            <h2>🧙 Follower Crafting (Enchantress)</h2>
            <p class="note">⚠️ Auf INT-Char craften (Wiz/WD/Necro) für richtigen Mainstat!</p>
            <div class="item"><input type="checkbox" id="fc1"><label for="fc1"><strong>Cain's Destiny</strong> (2pc) - Helm + Boots<br><span class="diff">+25% GR Key Drops (Emanate)</span></label></div>
            <div class="item"><input type="checkbox" id="fc2"><label for="fc2"><strong>Sage's Journey</strong> (2pc) - Helm + Boots oder Gloves<br><span class="diff">+1 Death's Breath (Emanate)</span></label></div>
            <div class="info-box">
                <strong>Weitere Emanate Items:</strong><br>
                • Nemesis Bracers - Elite bei Shrine<br>
                • Gloves of Worship - 10min Shrine (A2 Bounty)<br>
                • Flavor of Time - 2x Pylon Dauer<br>
                • Ring of Royal Grandeur - Set -1 (A1 Bounty)<br>
                • Oculus Ring - +85% Damage Circle<br>
                • Avarice Band - 30yd Pickup (A3 Bounty)
            </div>
            <p class="note">Templar → STR-Char (Barb/Sader), Scoundrel → DEX-Char (Monk/DH)</p>
        </div>'''


def main():
    parser = argparse.ArgumentParser(description='Generate D3 Season Guide HTML')
    parser.add_argument('--build', '-b', default='monk-sunwuko-tr',
                        help='Build file name (without .yaml)')
    parser.add_argument('--output', '-o', default='index.html',
                        help='Output HTML file')
    args = parser.parse_args()

    base_path = Path(__file__).parent

    # Load data files
    print(f"Loading data files...")
    static = load_yaml(base_path / 'd3-static-data.yaml')
    journey = load_yaml(base_path / 'season-journey-template.yaml')

    # Load season start guide
    start_guide_path = base_path / 'season-start-guide.yaml'
    start_guide = load_yaml(start_guide_path) if start_guide_path.exists() else None

    # Load glossary
    glossary_path = base_path / 'd3-glossary.yaml'
    glossary = load_yaml(glossary_path) if glossary_path.exists() else None

    build_file = base_path / f'{args.build}.yaml'
    if not build_file.exists():
        print(f"Error: Build file '{build_file}' not found!")
        print(f"Available builds:")
        for f in base_path.glob('*.yaml'):
            if f.name not in ['d3-static-data.yaml', 'season-journey-template.yaml']:
                print(f"  - {f.stem}")
        return 1

    build = load_yaml(build_file)

    # Merge boss data into journey
    journey = merge_boss_data(journey, static)

    # Generate HTML
    print(f"Generating HTML for {args.build}...")
    html = generate_html(static, journey, build, start_guide, glossary)

    # Write output
    output_path = base_path / args.output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == '__main__':
    exit(main())
