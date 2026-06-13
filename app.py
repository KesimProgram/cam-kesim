import streamlit as st
import pandas as pd
import json
import os
import streamlit.components.v1 as components

# --- KAYIT SİSTEMİ ---
KAYIT_DOSYASI = "kayitlar_cam.json"

def kayitlari_yukle():
    if os.path.exists(KAYIT_DOSYASI):
        with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def kayit_ekle(isim, list_data, palette_data):
    kayitlar = kayitlari_yukle()
    kayitlar[isim] = {"list": list_data, "palette": palette_data}
    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(kayitlar, f, ensure_ascii=False, indent=4)

def kayit_sil(isim):
    kayitlar = kayitlari_yukle()
    if isim in kayitlar:
        del kayitlar[isim]
        with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(kayitlar, f, ensure_ascii=False, indent=4)

# Geometrik Parçalama Motoru (Yeni Yapay Zekâ)
def filter_engulfed(rects):
    res = []
    rects = sorted(rects, key=lambda r: r['w'] * r['h'], reverse=True)
    for r in rects:
        is_inside = False
        for o in res:
            if r['x'] >= o['x'] - 0.01 and r['y'] >= o['y'] - 0.01 and r['x'] + r['w'] <= o['x'] + o['w'] + 0.01 and r['y'] + r['h'] <= o['y'] + o['h'] + 0.01:
                is_inside = True
                break
        if not is_inside:
            res.append(r)
    return res

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Cam Kesim İstasyonu", layout="wide")
st.title("🔮 İnteraktif Cam Kesim İstasyonu")

# Hafıza değişkenleri
if "cam_cinsi" not in st.session_state: st.session_state.cam_cinsi = "Düz Cam"
if "plaka_w" not in st.session_state: st.session_state.plaka_w = 321.0
if "plaka_h" not in st.session_state: st.session_state.plaka_h = 225.0
if 'df_cam' not in st.session_state:
    st.session_state.df_cam = pd.DataFrame({"En (cm)": [0.0], "Boy (cm)": [0.0], "Adet": [0]})

# --- SOL MENÜ AYARLAR ---
with st.sidebar:
    st.header("⚙️ Palet Ayarları")
    cam_turleri = ["Düz Cam", "Füme Cam", "Ayna"]
    cinsi_idx = cam_turleri.index(st.session_state.cam_cinsi) if st.session_state.cam_cinsi in cam_turleri else 0
    cam_secimi = st.selectbox("Cam Cinsi", cam_turleri, index=cinsi_idx, key="cinsi_widget")
    
    L_w = st.number_input("Ana Plaka Genişliği / En (cm)", value=st.session_state.plaka_w, step=1.0, key="w_widget")
    L_h = st.number_input("Ana Plaka Yüksekliği / Boy (cm)", value=st.session_state.plaka_h, step=1.0, key="h_widget")
    
    st.divider()
    rotation_aktif = st.checkbox("Algoritma Camları Döndürebilsin (90°)", value=True)
    
    # YENİ: KATI FİRE KURALLARI
    st.subheader("⚠️ Katı Fire Kuralları")
    fire_kural_aktif = st.checkbox("İstenmeyen Fire Ölçülerini Yasakla", value=False)
    if fire_kural_aktif:
        min_fire = st.number_input("Bu ölçüden BÜYÜK fire YASAK (Örn: 10)", value=10.0)
        max_fire = st.number_input("Bu ölçüden KÜÇÜK fire YASAK (Örn: 40)", value=40.0)
        st.info("💡 Sistem, hem EN hem de BOY olarak bu aralıkta fire bırakmamak için gerekirse yeni plaka açacaktır.")
    else:
        min_fire, max_fire = 0.0, 0.0
    
    st.divider()
    st.header("📂 Kayıtlı İşler")
    mevcut_kayitlar = kayitlari_yukle()
    if mevcut_kayitlar:
        secilen_kayit = st.selectbox("Kayıtlı Listeyi Yükle:", ["Seçiniz..."] + list(mevcut_kayitlar.keys()))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Yükle", use_container_width=True) and secilen_kayit != "Seçiniz...":
                data = mevcut_kayitlar[secilen_kayit]
                if isinstance(data, dict) and "list" in data:
                    st.session_state.df_cam = pd.DataFrame(data["list"])
                    st.session_state.cam_cinsi = data.get("palette", {}).get("cinsi", "Düz Cam")
                    st.session_state.plaka_w = float(data.get("palette", {}).get("w", 321.0))
                    st.session_state.plaka_h = float(data.get("palette", {}).get("h", 225.0))
                else:
                    st.session_state.df_cam = pd.DataFrame(data)
                st.rerun()
        with col2:
            if st.button("🗑️ Sil", use_container_width=True) and secilen_kayit != "Seçiniz...":
                kayit_sil(secilen_kayit)
                st.success("Silindi!")
                st.rerun()

# --- SİPARİŞ TABLOSU ---
st.subheader(f"📋 Kesilecek {cam_secimi} Ölçüleri")
df_giris = st.data_editor(st.session_state.df_cam, num_rows="dynamic", use_container_width=True)

# KAYDETME
st.write("---")
col_isim, col_kaydet = st.columns([3, 1])
with col_isim: kayit_ismi = st.text_input("Bu listeyi kaydetmek istersen isim ver:")
with col_kaydet:
    st.write(""); st.write("")
    if st.button("💾 Bilgileri Kaydet", use_container_width=True):
        if kayit_ismi:
            df_gecerli = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)]
            palette_info = {"cinsi": cam_secimi, "w": L_w, "h": L_h}
            kayit_ekle(kayit_ismi, df_gecerli.to_dict('records'), palette_info)
            st.success("Liste ve Palet Ayarları kaydedildi!")
        else: st.warning("İsim girmelisiniz.")
st.write("---")

# --- HESAPLAMA MOTORU (MİNİMUM PLAKA ALGORİTMASI) ---
if st.button("🚀 Haritayı Çiz & Düzenlemeye Başla", type="primary"):
    df_temiz = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)].copy()
    
    if df_temiz.empty:
        st.warning("Lütfen geçerli cam ölçüleri girin.")
    else:
        with st.spinner("Yapay Zekâ Motoru çalışıyor, camlar tetris gibi paketleniyor..."):
            all_pieces = []
            for _, row in df_temiz.iterrows():
                for _ in range(int(row["Adet"])):
                    all_pieces.append({"w": row["En (cm)"], "h": row["Boy (cm)"]})
            
            # En büyük parçaları önce yerleştirerek plaka israfını sıfırlıyoruz
            all_pieces.sort(key=lambda x: max(x["w"], x["h"]), reverse=True)
            
            plates = []
            for piece in all_pieces:
                best_plate_idx = -1
                best_rect = None
                best_rotated = False
                best_score = float('inf')

                # Önce mevcut plakalara sığdırmaya çalış
                for i, plate in enumerate(plates):
                    for fr in plate['free_rects']:
                        # Normal Yön
                        if piece['w'] <= fr['w'] + 0.01 and piece['h'] <= fr['h'] + 0.01:
                            rem_w = fr['w'] - piece['w']
                            rem_h = fr['h'] - piece['h']
                            score = min(rem_w, rem_h)
                            if fire_kural_aktif:
                                if min_fire < rem_w < max_fire: score += 1000000
                                if min_fire < rem_h < max_fire: score += 1000000
                            if score < best_score:
                                best_score = score; best_rect = fr; best_rotated = False; best_plate_idx = i

                        # Döndürülmüş Yön
                        if rotation_aktif and piece['h'] <= fr['w'] + 0.01 and piece['w'] <= fr['h'] + 0.01:
                            rem_w = fr['w'] - piece['h']
                            rem_h = fr['h'] - piece['w']
                            score = min(rem_w, rem_h)
                            if fire_kural_aktif:
                                if min_fire < rem_w < max_fire: score += 1000000
                                if min_fire < rem_h < max_fire: score += 1000000
                            if score < best_score:
                                best_score = score; best_rect = fr; best_rotated = True; best_plate_idx = i

                # Yepyeni bir plaka açmanın maliyeti (Fire yasağına takılırsa yeni plaka açmayı tercih eder)
                new_score_n = float('inf')
                new_score_r = float('inf')
                if piece['w'] <= L_w and piece['h'] <= L_h:
                    s_n = min(L_w - piece['w'], L_h - piece['h'])
                    if fire_kural_aktif:
                        if min_fire < (L_w - piece['w']) < max_fire: s_n += 1000000
                        if min_fire < (L_h - piece['h']) < max_fire: s_n += 1000000
                    s_n += 400000 # Yeni plaka açma maliyeti (Cezadan düşük)
                    new_score_n = s_n

                if rotation_aktif and piece['h'] <= L_w and piece['w'] <= L_h:
                    s_r = min(L_w - piece['h'], L_h - piece['w'])
                    if fire_kural_aktif:
                        if min_fire < (L_w - piece['h']) < max_fire: s_r += 1000000
                        if min_fire < (L_h - piece['w']) < max_fire: s_r += 1000000
                    s_r += 400000
                    new_score_r = s_r

                # Eğer yeni plaka açmak, mevcut plakada fire yasağı yemekten daha avantajlıysa, yeni plaka aç!
                best_new = min(new_score_n, new_score_r)
                if best_new < best_score:
                    best_plate_idx = -1
                    best_rotated = new_score_r < new_score_n

                if best_plate_idx != -1:
                    pw, ph = (piece['h'], piece['w']) if best_rotated else (piece['w'], piece['h'])
                    px, py = best_rect['x'], best_rect['y']
                    target_plate = plates[best_plate_idx]
                    target_plate['items'].append({'x': px, 'y': py, 'w': pw, 'h': ph})

                    new_free = []
                    for fr in target_plate['free_rects']:
                        if not (px >= fr['x'] + fr['w'] or px + pw <= fr['x'] or py >= fr['y'] + fr['h'] or py + ph <= fr['y']):
                            if px > fr['x']: new_free.append({'x': fr['x'], 'y': fr['y'], 'w': px - fr['x'], 'h': fr['h']})
                            if px + pw < fr['x'] + fr['w']: new_free.append({'x': px + pw, 'y': fr['y'], 'w': fr['x'] + fr['w'] - (px + pw), 'h': fr['h']})
                            if py > fr['y']: new_free.append({'x': fr['x'], 'y': fr['y'], 'w': fr['w'], 'h': py - fr['y']})
                            if py + ph < fr['y'] + fr['h']: new_free.append({'x': fr['x'], 'y': py + ph, 'w': fr['w'], 'h': fr['y'] + fr['h'] - (py + ph)})
                        else:
                            new_free.append(fr)
                    target_plate['free_rects'] = filter_engulfed(new_free)
                else:
                    new_plate = {'items': [], 'free_rects': [{'x': 0, 'y': 0, 'w': L_w, 'h': L_h}]}
                    pw, ph = (piece['h'], piece['w']) if best_rotated else (piece['w'], piece['h'])
                    new_plate['items'].append({'x': 0, 'y': 0, 'w': pw, 'h': ph})
                    new_free = []
                    if pw < L_w: new_free.append({'x': pw, 'y': 0, 'w': L_w - pw, 'h': L_h})
                    if ph < L_h: new_free.append({'x': 0, 'y': ph, 'w': L_w, 'h': L_h - ph})
                    new_plate['free_rects'] = filter_engulfed(new_free)
                    plates.append(new_plate)

            st.success(f"✅ Paketleme Tamamlandı! Toplam Kullanılan Plaka: {len(plates)} Adet")
            
            job_id_name = kayit_ismi if kayit_ismi else "gecici_islem"
            
            html_code = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <style>
              * {{ box-sizing: border-box; }}
              body {{ margin: 0; padding: 0; font-family: sans-serif; background: transparent; padding-bottom: 50px; }}
              .toolbar {{
                  background-color: #f1faee; border: 2px solid #a8dadc; border-radius: 5px;
                  padding: 15px; margin-bottom: 20px; text-align: center; width: 900px; max-width: 100%; margin-left: auto; margin-right: auto;
                  display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;
              }}
              .action-btn {{
                  color: white; border: none; border-radius: 5px; padding: 10px 15px; font-size: 15px; font-weight: bold; cursor: pointer;
                  box-shadow: 2px 2px 5px rgba(0,0,0,0.3); transition: 0.2s;
              }}
              .action-btn:active {{ transform: scale(0.95); }}
              .rotate-btn {{ background-color: #1d3557; }}
              .rotate-btn:hover {{ background-color: #457b9d; }}
              .save-btn {{ background-color: #2a9d8f; }}
              .save-btn:hover {{ background-color: #21867a; }}
              .pdf-btn {{ background-color: #e63946; }}
              .pdf-btn:hover {{ background-color: #d62828; }}
              
              .plate-title {{ font-size: 22px; font-weight: bold; color: #333; margin: 20px auto 5px auto; font-family: sans-serif; width: 900px; max-width: 100%; }}
              
              /* KESİLMEYİ ÖNLEYEN SABİT PİKSEL GENİŞLİK */
              .plate-wrapper {{
                  position: relative; width: 900px; max-width: 100%; height: {(L_h / L_w) * 900}px;
                  margin: 0 auto 30px auto;
                  background-color: #2b2b2b; border: 4px solid #1e1e1e;
                  touch-action: none; overflow: hidden; border-radius: 4px;
              }}
              .piece {{
                  position: absolute; background-color: rgba(42, 157, 143, 0.95);
                  border: 1px solid #fff; display: flex; align-items: center; justify-content: center;
                  color: white; font-weight: bold; font-size: 14px; text-align: center; line-height: 1.2;
                  cursor: grab; user-select: none; transition: box-shadow 0.2s; z-index: 10;
              }}
              .piece.selected {{ box-shadow: 0px 0px 0px 4px #e63946 inset; z-index: 1000; background-color: rgba(69, 123, 157, 0.95); }}
              .piece:active {{ cursor: grabbing; }}
              
              .waste {{
                  position: absolute; background: repeating-linear-gradient(45deg, #3a3a3a, #3a3a3a 10px, #4a4a4a 10px, #4a4a4a 20px);
                  border: 2px dashed #888; display: flex; align-items: center; justify-content: center;
                  color: #ccc; font-weight: bold; font-size: 13px; text-align: center; line-height: 1.2;
                  pointer-events: none; opacity: 0.9; z-index: 1;
              }}
              
              @media print {{
                  body {{ background: white !important; margin: 0; padding: 0; }}
                  .no-print {{ display: none !important; }}
                  .plate-wrapper {{ background-color: #f9f9f9 !important; border: 2px solid black !important; page-break-after: always; margin-bottom: 20px; }}
                  .piece {{ background-color: #e0e0e0 !important; color: black !important; border: 1px solid black !important; font-size: 12px; }}
                  .waste {{ background: none !important; color: #555 !important; border: 1px dashed black !important; }}
                  .plate-title {{ color: black; }}
                  .piece.selected {{ box-shadow: none !important; border: 1px solid black !important; }}
              }}
            </style>
            </head>
            <body>
            
            <div class="toolbar no-print">
                <button class="action-btn rotate-btn" onclick="rotateSelected()">🔄 Seçili Camı Döndür</button>
                <button class="action-btn save-btn" onclick="saveLayout()">💾 Yerleşimi Tarayıcıya Kaydet</button>
                <button class="action-btn pdf-btn" onclick="window.print()">🖨️ PDF Al / Yazdır</button>
                <div style="width:100%; font-size:12px; color:#555; margin-top:5px;">(Seçimi bırakmak için gri fire alanlarına veya boşluğa tıklayabilirsin)</div>
            </div>
            """
            
            for p_idx, plate in enumerate(plates):
                html_code += f'<div class="plate-title">Plaka {p_idx+1} ({L_w}x{L_h} cm) - {cam_secimi}</div>'
                html_code += f'<div class="plate-wrapper" id="plate_{p_idx}" data-pw="{L_w}" data-ph="{L_h}">'
                
                for i_idx, item in enumerate(plate["items"]):
                    p_id = f"piece_{p_idx}_{i_idx}"
                    left_pct = (item["x"] / L_w) * 100
                    top_pct = (item["y"] / L_h) * 100
                    w_pct = (item["w"] / L_w) * 100
                    h_pct = (item["h"] / L_h) * 100
                    html_code += f'<div id="{p_id}" class="piece" style="left:{left_pct}%; top:{top_pct}%; width:{w_pct}%; height:{h_pct}%;" data-w="{item["w"]}" data-h="{item["h"]}" onclick="selectPiece(event, this)">↔ {item["w"]}<br>↕ {item["h"]}</div>'
                
                html_code += '</div>'
            
            html_code += f"""
            <script>
              let dragged = null;
              let selected = null;
              let startX, startY, startLeft, startTop;
              let jobKey = "cam_layout_{job_id_name}";

              document.addEventListener('mousedown', function(e) {{
                  if (!e.target.classList.contains('piece') && selected) {{
                      selected.classList.remove('selected');
                      selected = null;
                  }}
              }});
              document.addEventListener('touchstart', function(e) {{
                  if (!e.target.classList.contains('piece') && selected) {{
                      selected.classList.remove('selected');
                      selected = null;
                  }}
              }}, {{passive: true}});

              function saveLayout() {{
                  let layout = [];
                  document.querySelectorAll('.piece').forEach(p => {{
                      layout.push({{
                          id: p.id, left: p.style.left, top: p.style.top,
                          width: p.style.width, height: p.style.height,
                          dataW: p.getAttribute('data-w'), dataH: p.getAttribute('data-h'),
                          innerHTML: p.innerHTML
                      }});
                  }});
                  localStorage.setItem(jobKey, JSON.stringify(layout));
                  alert("Dizilim tarayıcıya kaydedildi! Programı kapatıp açsanız veya 'Yükle' deseniz bile, bu iş ismiyle camlar tam bıraktığınız yerde açılacak.");
              }}

              function loadLayout() {{
                  let saved = localStorage.getItem(jobKey);
                  if (saved) {{
                      let layout = JSON.parse(saved);
                      layout.forEach(item => {{
                          let p = document.getElementById(item.id);
                          if (p) {{
                              p.style.left = item.left; p.style.top = item.top;
                              p.style.width = item.width; p.style.height = item.height;
                              p.setAttribute('data-w', item.dataW); p.setAttribute('data-h', item.dataH);
                              p.innerHTML = item.innerHTML;
                          }}
                      }});
                  }}
              }}

              function updateWaste() {{
                  document.querySelectorAll('.plate-wrapper').forEach(plateDiv => {{
                      plateDiv.querySelectorAll('.waste').forEach(e => e.remove());
                      let plateW = parseFloat(plateDiv.getAttribute('data-pw'));
                      let plateH = parseFloat(plateDiv.getAttribute('data-ph'));

                      let pieces = [];
                      plateDiv.querySelectorAll('.piece').forEach(p => {{
                          let w = parseFloat(p.getAttribute('data-w'));
                          let h = parseFloat(p.getAttribute('data-h'));
                          let l = (parseFloat(p.style.left) / 100) * plateW;
                          let t = (parseFloat(p.style.top) / 100) * plateH;
                          pieces.push({{l: l, t: t, r: l+w, b: t+h}});
                      }});

                      let freeRects = [{{l:0, t:0, r:plateW, b:plateH}}];
                      let eps = 0.5;

                      pieces.forEach(p => {{
                          let nextFree = [];
                          freeRects.forEach(e => {{
                              if (p.l < e.r - eps && p.r > e.l + eps && p.t < e.b - eps && p.b > e.t + eps) {{
                                  if (p.t > e.t + eps) nextFree.push({{l: e.l, t: e.t, r: e.r, b: p.t}});
                                  if (p.b < e.b - eps) nextFree.push({{l: e.l, t: p.b, r: e.r, b: e.b}});
                                  if (p.l > e.l + eps) nextFree.push({{l: e.l, t: e.t, r: p.l, b: e.b}});
                                  if (p.r < e.r - eps) nextFree.push({{l: p.r, t: e.t, r: e.r, b: e.b}});
                              }} else {{
                                  nextFree.push(e);
                              }}
                          }});
                          freeRects = nextFree;
                      }});

                      let finalWaste = [];
                      while(freeRects.length > 0) {{
                          freeRects.forEach(r => r.area = (r.r - r.l) * (r.b - r.t));
                          freeRects.sort((a,b) => b.area - a.area);
                          
                          let best = freeRects.shift();
                          // Minik yolluk firelerini bile çizgili gösterebilmek için alt sınırı çok düşürdük
                          if (best.r - best.l < 1 || best.b - best.t < 1) continue;
                          
                          finalWaste.push(best);
                          
                          let nextFree = [];
                          freeRects.forEach(r => {{
                              let sub = best;
                              if (r.r <= sub.l+eps || r.l >= sub.r-eps || r.b <= sub.t+eps || r.t >= sub.b-eps) {{
                                  nextFree.push(r);
                              }} else {{
                                  if (r.t < sub.t) nextFree.push({{l: r.l, t: r.t, r: r.r, b: sub.t}});
                                  if (r.b > sub.b) nextFree.push({{l: r.l, t: sub.b, r: r.r, b: r.b}});
                                  if (r.l < sub.l) nextFree.push({{l: r.l, t: Math.max(r.t, sub.t), r: sub.l, b: Math.min(r.b, sub.b)}});
                                  if (r.r > sub.r) nextFree.push({{l: sub.r, t: Math.max(r.t, sub.t), r: r.r, b: Math.min(r.b, sub.b)}});
                              }}
                          }});
                          freeRects = nextFree;
                      }}

                      finalWaste.forEach(w => {{
                          let div = document.createElement('div');
                          div.className = 'waste';
                          div.style.left = ((w.l / plateW) * 100) + '%';
                          div.style.top = ((w.t / plateH) * 100) + '%';
                          
                          let wasteW = w.r - w.l;
                          let wasteH = w.b - w.t;
                          
                          div.style.width = ((wasteW / plateW) * 100) + '%';
                          div.style.height = ((wasteH / plateH) * 100) + '%';
                          
                          // 5 cm'den küçük firelere sadece taralı alan atıyoruz, yazıyla kalabalık etmiyoruz!
                          if (wasteW >= 5 && wasteH >= 5) {{
                              div.innerHTML = 'FİRE<br>↔ ' + wasteW.toFixed(1) + '<br>↕ ' + wasteH.toFixed(1);
                          }} else {{
                              div.innerHTML = ''; 
                          }}
                          
                          plateDiv.appendChild(div);
                      }});
                  }});
              }}

              function selectPiece(e, el) {{
                  e.stopPropagation();
                  if (selected) {{ selected.classList.remove('selected'); }}
                  selected = el;
                  selected.classList.add('selected');
              }}

              function rotateSelected() {{
                  if (!selected) {{ alert("Lütfen döndürmek için önce plakadaki cama tıklayın!"); return; }}
                  let plateDiv = selected.parentElement;
                  let plateW = parseFloat(plateDiv.getAttribute('data-pw'));
                  let plateH = parseFloat(plateDiv.getAttribute('data-ph'));
                  
                  let oldW = parseFloat(selected.getAttribute('data-w'));
                  let oldH = parseFloat(selected.getAttribute('data-h'));
                  let newW = oldH, newH = oldW;
                  
                  let newW_pct = (newW / plateW) * 100;
                  let newH_pct = (newH / plateH) * 100;
                  let currentLeft = parseFloat(selected.style.left) || 0;
                  let currentTop = parseFloat(selected.style.top) || 0;
                  
                  if (currentLeft + newW_pct > 100) currentLeft = 100 - newW_pct;
                  if (currentTop + newH_pct > 100) currentTop = 100 - newH_pct;
                  
                  selected.setAttribute('data-w', newW);
                  selected.setAttribute('data-h', newH);
                  selected.style.width = newW_pct + "%";
                  selected.style.height = newH_pct + "%";
                  selected.style.left = currentLeft + "%";
                  selected.style.top = currentTop + "%";
                  selected.innerHTML = "↔ " + newW + "<br>↕ " + newH;
                  
                  updateWaste();
              }}

              function startDrag(e) {{
                  if(!e.target.classList.contains('piece')) return;
                  selectPiece(e, e.target);
                  dragged = e.target;
                  let clientX = e.touches ? e.touches[0].clientX : e.clientX;
                  let clientY = e.touches ? e.touches[0].clientY : e.clientY;
                  startX = clientX; startY = clientY;
                  startLeft = parseFloat(dragged.style.left) || 0;
                  startTop = parseFloat(dragged.style.top) || 0;
              }}

              function drag(e) {{
                  if (!dragged) return;
                  e.preventDefault(); 
                  let clientX = e.touches ? e.touches[0].clientX : e.clientX;
                  let clientY = e.touches ? e.touches[0].clientY : e.clientY;
                  let dx = clientX - startX; let dy = clientY - startY;

                  let parentRect = dragged.parentElement.getBoundingClientRect();
                  let dxPercent = (dx / parentRect.width) * 100;
                  let dyPercent = (dy / parentRect.height) * 100;

                  let newLeft = startLeft + dxPercent; let newTop = startTop + dyPercent;
                  let wPercent = parseFloat(dragged.style.width); let hPercent = parseFloat(dragged.style.height);

                  let snapThreshold = 1.5; 
                  let pieces = dragged.parentElement.querySelectorAll('.piece');
                  let newRight = newLeft + wPercent; let newBottom = newTop + hPercent;
                  
                  if (newLeft < snapThreshold) newLeft = 0;
                  if (newTop < snapThreshold) newTop = 0;
                  if (100 - newRight < snapThreshold) newLeft = 100 - wPercent;
                  if (100 - newBottom < snapThreshold) newTop = 100 - hPercent;

                  pieces.forEach(p => {{
                      if(p === dragged) return;
                      let pLeft = parseFloat(p.style.left); let pTop = parseFloat(p.style.top);
                      let pRight = pLeft + parseFloat(p.style.width); let pBottom = pTop + parseFloat(p.style.height);

                      if (Math.abs(newLeft - pRight) < snapThreshold) newLeft = pRight;
                      if (Math.abs(newRight - pLeft) < snapThreshold) newLeft = pLeft - wPercent;
                      if (Math.abs(newLeft - pLeft) < snapThreshold) newLeft = pLeft;
                      if (Math.abs(newTop - pBottom) < snapThreshold) newTop = pBottom;
                      if (Math.abs(newBottom - pTop) < snapThreshold) newTop = pTop - hPercent;
                      if (Math.abs(newTop - pTop) < snapThreshold) newTop = pTop;
                  }});

                  dragged.style.left = newLeft + '%'; dragged.style.top = newTop + '%';
              }}

              function endDrag(e) {{
                  if (dragged) {{ dragged = null; updateWaste(); }}
              }}

              document.addEventListener('mousedown', startDrag);
              document.addEventListener('mousemove', drag);
              document.addEventListener('mouseup', endDrag);
              document.addEventListener('touchstart', startDrag, {{passive: false}});
              document.addEventListener('touchmove', drag, {{passive: false}});
              document.addEventListener('touchend', endDrag);
              
              window.onload = function() {{
                  loadLayout(); 
                  setTimeout(updateWaste, 100); 
              }};
            </script>
            </body>
            </html>
            """
            
            # Dinamik yükseklik: Kesilmeyi kökten çözen formül
            plaka_h_px = (L_h / L_w) * 900
            toplam_yukseklik = 150 + len(plates) * (plaka_h_px + 70)
            components.html(html_code, height=int(toplam_yukseklik))
