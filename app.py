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

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Cam Kesim İstasyonu", layout="wide")
st.title("🔮 İnteraktif Cam Kesim İstasyonu")

# Hafıza değişkenleri (Yükleme yapıldığında otomatik değişmesi için)
if "selected_cinsi" not in st.session_state: st.session_state.selected_cinsi = "Düz Cam"
if "selected_w" not in st.session_state: st.session_state.selected_w = 321.0
if "selected_h" not in st.session_state: st.session_state.selected_h = 225.0
if 'df_cam' not in st.session_state:
    st.session_state.df_cam = pd.DataFrame({"En (cm)": [0.0], "Boy (cm)": [0.0], "Adet": [0]})

# --- SOL MENÜ AYARLAR ---
with st.sidebar:
    st.header("⚙️ Palet Ayarları")
    
    cam_turleri = ["Düz Cam", "Füme Cam", "Ayna"]
    cinsi_idx = cam_turleri.index(st.session_state.selected_cinsi) if st.session_state.selected_cinsi in cam_turleri else 0
    cam_secimi = st.selectbox("Cam Cinsi", cam_turleri, index=cinsi_idx)
    
    L_w = st.number_input("Ana Plaka Genişliği / En (cm)", value=st.session_state.selected_w, step=1.0)
    L_h = st.number_input("Ana Plaka Yüksekliği / Boy (cm)", value=st.session_state.selected_h, step=1.0)
    
    st.divider()
    rotation_aktif = st.checkbox("Algoritma Camları Döndürebilsin (90°)", value=True)
    
    st.divider()
    st.header("📂 Kayıtlı İşler")
    mevcut_kayitlar = kayitlari_yukle()
    if mevcut_kayitlar:
        secilen_kayit = st.selectbox("Kayıtlı Listeyi Yükle:", ["Seçiniz..."] + list(mevcut_kayitlar.keys()))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Yükle", use_container_width=True) and secilen_kayit != "Seçiniz...":
                data = mevcut_kayitlar[secilen_kayit]
                # Eski sürüm kayıtları veya yeni sürüm kayıtları ayırma
                if isinstance(data, dict) and "list" in data:
                    st.session_state.df_cam = pd.DataFrame(data["list"])
                    st.session_state.selected_cinsi = data.get("palette", {}).get("cinsi", "Düz Cam")
                    st.session_state.selected_w = data.get("palette", {}).get("w", 321.0)
                    st.session_state.selected_h = data.get("palette", {}).get("h", 225.0)
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
with col_isim:
    kayit_ismi = st.text_input("Bu listeyi kaydetmek istersen isim ver:")
with col_kaydet:
    st.write("") 
    st.write("")
    if st.button("💾 Bilgileri Kaydet", use_container_width=True):
        if kayit_ismi:
            df_gecerli = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)]
            palette_info = {"cinsi": cam_secimi, "w": L_w, "h": L_h}
            kayit_ekle(kayit_ismi, df_gecerli.to_dict('records'), palette_info)
            st.success("Liste ve Palet Ayarları kaydedildi!")
        else:
            st.warning("İsim girmelisiniz.")
st.write("---")

# --- HESAPLAMA MOTORU ---
if st.button("🚀 Haritayı Çiz & Düzenlemeye Başla", type="primary"):
    df_temiz = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)].copy()
    
    if df_temiz.empty:
        st.warning("Lütfen geçerli cam ölçüleri girin.")
    else:
        with st.spinner("Camlar plakaya diziliyor..."):
            all_pieces = []
            for _, row in df_temiz.iterrows():
                for _ in range(int(row["Adet"])):
                    all_pieces.append({"w": row["En (cm)"], "h": row["Boy (cm)"]})
            
            if rotation_aktif:
                for p in all_pieces:
                    if p["w"] < p["h"]: p["w"], p["h"] = p["h"], p["w"]
            
            all_pieces.sort(key=lambda x: x["h"], reverse=True)
            
            plates = []
            for piece in all_pieces:
                w, h = piece["w"], piece["h"]
                placed = False
                
                for plate in plates:
                    for shelf in plate["shelves"]:
                        if shelf["x_used"] + w <= L_w and h <= shelf["height"]:
                            plate["items"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": w, "h": h})
                            shelf["x_used"] += w
                            placed = True; break
                        elif rotation_aktif and shelf["x_used"] + h <= L_w and w <= shelf["height"]:
                            plate["items"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": h, "h": w})
                            shelf["x_used"] += h
                            placed = True; break
                    if placed: break
                    
                    if plate["y_used"] + h <= L_h and w <= L_w:
                        new_shelf = {"y_start": plate["y_used"], "height": h, "x_used": w}
                        plate["items"].append({"x": 0, "y": plate["y_used"], "w": w, "h": h})
                        plate["shelves"].append(new_shelf)
                        plate["y_used"] += h
                        placed = True; break
                    elif rotation_aktif and plate["y_used"] + w <= L_h and h <= L_w:
                        new_shelf = {"y_start": plate["y_used"], "height": w, "x_used": h}
                        plate["items"].append({"x": 0, "y": plate["y_used"], "w": h, "h": w})
                        plate["shelves"].append(new_shelf)
                        plate["y_used"] += w
                        placed = True; break
                
                if not placed:
                    new_plate = {"shelves": [], "y_used": 0, "items": []}
                    if w <= L_w and h <= L_h:
                        new_shelf = {"y_start": 0, "height": h, "x_used": w}
                        new_plate["items"].append({"x": 0, "y": 0, "w": w, "h": h})
                        new_plate["shelves"].append(new_shelf)
                        new_plate["y_used"] += h
                        plates.append(new_plate)
                    elif rotation_aktif and h <= L_w and w <= L_h:
                        new_shelf = {"y_start": 0, "height": w, "x_used": h}
                        new_plate["items"].append({"x": 0, "y": 0, "w": h, "h": w})
                        new_plate["shelves"].append(new_shelf)
                        new_plate["y_used"] += w
                        plates.append(new_plate)
                    else:
                        st.error(f"❌ Hata: {w}x{h} ölçüsü {L_w}x{L_h} ana plakadan büyük!")
                        st.stop()

            st.success(f"✅ Kesim Haritası Hazır! Toplam Plaka: {len(plates)} Adet")
            
            # --- TEK PARÇA DEV İNTERAKTİF HTML ---
            # Artık tüm plakalar tek bir pencerede toplanıyor ki PDF ve Kayıt sistemi sorunsuz çalışsın.
            
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
                  padding: 15px; margin-bottom: 20px; text-align: center; width: 100%; display: flex;
                  justify-content: center; gap: 10px; flex-wrap: wrap;
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
              
              .plate-title {{ font-size: 22px; font-weight: bold; color: #333; margin: 20px 0 5px 0; font-family: sans-serif; }}
              .plate-wrapper {{
                  position: relative; width: 100%; padding-bottom: {(L_h / L_w) * 100}%;
                  background-color: #2b2b2b; border: 4px solid #1e1e1e; box-sizing: content-box;
                  touch-action: none; overflow: hidden; border-radius: 4px; margin-bottom: 30px;
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
              
              /* PDF VE YAZDIRMA AYARLARI */
              @media print {{
                  body {{ background: white !important; margin: 0; padding: 0; }}
                  .no-print {{ display: none !important; }}
                  .plate-wrapper {{ background-color: #f9f9f9 !important; border: 2px solid black !important; page-break-after: always; margin-bottom: 20px; }}
                  .piece {{ background-color: #e0e0e0 !important; color: black !important; border: 1px solid black !important; font-size: 12px; }}
                  .waste {{ background: none !important; color: #555 !important; border: 1px dashed black !important; }}
                  .plate-title {{ color: black; }}
                  .piece.selected {{ box-shadow: none !important; border: 1px solid black !important; }}
              }}
              
              @media (max-width: 600px) {{ .piece, .waste {{ font-size: 10px; }} }}
            </style>
            </head>
            <body>
            
            <div class="toolbar no-print">
                <button class="action-btn rotate-btn" onclick="rotateSelected()">🔄 Seçili Camı Döndür</button>
                <button class="action-btn save-btn" onclick="saveLayout()">💾 Yerleşimi Tarayıcıya Kaydet</button>
                <button class="action-btn pdf-btn" onclick="window.print()">🖨️ PDF Al / Yazdır</button>
                <div style="width:100%; font-size:12px; color:#555; margin-top:5px;">(Seçimi bırakmak için gri fire alanlarına tıklayabilirsin)</div>
            </div>
            """
            
            # TÜM PLAKALARI TEK DÖNGÜDE HTML İÇİNE YAZDIRMA
            for p_idx, plate in enumerate(plates):
                html_code += f'<div class="plate-title">Plaka {p_idx+1} ({L_w}x{L_h} cm) - {cam_secimi}</div>'
                html_code += f'<div class="plate-wrapper" id="plate_{p_idx}" data-pw="{L_w}" data-ph="{L_h}">'
                
                for i_idx, item in enumerate(plate["items"]):
                    p_id = f"piece_{p_idx}_{i_idx}" # Eşsiz kimlik oluşturduk ki kaydederken bulalım
                    left_pct = (item["x"] / L_w) * 100
                    top_pct = (item["y"] / L_h) * 100
                    w_pct = (item["w"] / L_w) * 100
                    h_pct = (item["h"] / L_h) * 100
                    html_code += f'<div id="{p_id}" class="piece" style="left:{left_pct}%; top:{top_pct}%; width:{w_pct}%; height:{h_pct}%;" data-w="{item["w"]}" data-h="{item["h"]}" onclick="selectPiece(event, this)">↔ {item["w"]}<br>↕ {item["h"]}</div>'
                
                html_code += '</div>'
            
            # JAVASCRIPT MOTORU
            html_code += f"""
            <script>
              let dragged = null;
              let selected = null;
              let startX, startY, startLeft, startTop;
              let jobKey = "cam_layout_{job_id_name}";

              // --- BOŞ YERE TIKLAYINCA SEÇİMİ İPTAL ETME ---
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

              // --- MANUEL YERLEŞİMİ KAYDETME VE YÜKLEME ---
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
                  alert("Dizilim tarayıcı hafızasına kaydedildi! Sayfayı yenilediğinizde (veya Yükle dediğinizde) camlar aynen bıraktığınız gibi gelecektir.");
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

              // --- KUSURSUZ (ÇOKLU) FİRE BÖLÜCÜ MOTOR ---
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
                          if (best.area < 15) continue;
                          if (best.r - best.l < 3 || best.b - best.t < 3) continue;
                          
                          finalWaste.push(best);
                          
                          let nextFree = [];
                          freeRects.forEach(r => {{
                              let sub = best;
                              if (r.r <= sub.l+eps || r.l >= sub.r-eps || r.b <= sub.t+eps || r.t >= sub.b-eps) {{
                                  nextFree.push(r);
                              }} else {{
                                  if (r.t < sub.t) nextFree.push({{l: r.l, t: r.t, r: r.r, b: sub.t}});
                                  if (r.b > sub.b) nextFree.push({{l: r.l, t: sub.b, r: r.r, b: r.b}});
                                  if (r.l < sub.l) nextFree.push({{l: r.l, t: Math.max(r.t, sub.t), r: sub.l, b: Math.min(r.b, sub.b)});
                                  if (r.r > sub.r) nextFree.push({{l: sub.r, t: Math.max(r.t, sub.t), r: r.r, b: Math.min(r.b, sub.b)});
                              }}
                          }});
                          freeRects = nextFree;
                      }}

                      finalWaste.forEach(w => {{
                          let div = document.createElement('div');
                          div.className = 'waste';
                          div.style.left = ((w.l / plateW) * 100) + '%';
                          div.style.top = ((w.t / plateH) * 100) + '%';
                          div.style.width = (((w.r - w.l) / plateW) * 100) + '%';
                          div.style.height = (((w.b - w.t) / plateH) * 100) + '%';
                          div.innerHTML = 'FİRE<br>↔ ' + (w.r - w.l).toFixed(1) + '<br>↕ ' + (w.b - w.t).toFixed(1);
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
                  loadLayout(); // Varsa kayıtlı dizilimi geri yükler
                  setTimeout(updateWaste, 100); // Fireleri anında hesaplar
              }};
            </script>
            </body>
            </html>
            """
            
            # Dinamik yüksekliği tüm plakalara yetecek şekilde ayarlıyoruz.
            # Kesik çıkma sorunu burada çözülüyor!
            toplam_yukseklik = 150 + len(plates) * ((L_h / L_w) * 850 + 120)
            components.html(html_code, height=int(toplam_yukseklik))
