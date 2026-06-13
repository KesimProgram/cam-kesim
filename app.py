import streamlit as st
import pandas as pd
import numpy as np
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

def kayit_ekle(isim, data):
    kayitlar = kayitlari_yukle()
    kayitlar[isim] = data
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
st.title("🔮 İnteraktif Cam Kesim ve Palet Dizilim İstasyonu")

if 'df_cam' not in st.session_state:
    st.session_state.df_cam = pd.DataFrame({"En (cm)": [0.0], "Boy (cm)": [0.0], "Adet": [0]})

# --- SOL MENÜ AYARLAR ---
with st.sidebar:
    st.header("⚙️ Palet Ayarları")
    
    # Cam Cinsi Seçimi
    cam_turleri = {
        "Düz Cam": (321.0, 225.0),
        "Füme Cam": (321.0, 225.0),
        "Ayna": (321.0, 225.0)
    }
    cam_secimi = st.selectbox("Cam Cinsi", list(cam_turleri.keys()))
    varsayilan_w, varsayilan_h = cam_turleri[cam_secimi]
    
    L_w = st.number_input("Ana Plaka Genişliği / En (cm)", value=varsayilan_w, step=1.0)
    L_h = st.number_input("Ana Plaka Yüksekliği / Boy (cm)", value=varsayilan_h, step=1.0)
    
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
                st.session_state.df_cam = pd.DataFrame(mevcut_kayitlar[secilen_kayit])
                st.rerun()
        with col2:
            if st.button("🗑️ Sil", use_container_width=True) and secilen_kayit != "Seçiniz...":
                kayit_sil(secilen_kayit)
                st.success("Silindi!")
                st.rerun()

# --- SİPARİŞ TABLOSU ---
st.subheader("📋 Kesilecek Cam Ölçüleri")
df_giris = st.data_editor(st.session_state.df_cam, num_rows="dynamic", use_container_width=True)

# KAYDETME
st.write("---")
col_isim, col_kaydet = st.columns([3, 1])
with col_isim:
    kayit_ismi = st.text_input("Bu listeyi kaydetmek istersen isim ver:")
with col_kaydet:
    st.write("") 
    st.write("")
    if st.button("💾 Kaydet", use_container_width=True):
        if kayit_ismi:
            df_gecerli = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)]
            kayit_ekle(kayit_ismi, df_gecerli.to_dict('records'))
            st.success("Liste kaydedildi!")
        else:
            st.warning("İsim girmelisiniz.")
st.write("---")

# --- HESAPLAMA MOTORU ---
if st.button("🚀 Haritayı Çiz & Mıknatıslı Düzenlemeye Başla", type="primary"):
    df_temiz = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)].copy()
    
    if df_temiz.empty:
        st.warning("Lütfen geçerli cam ölçüleri girin.")
    else:
        with st.spinner("Camlar plakaya diziliyor..."):
            all_pieces = []
            for _, row in df_temiz.iterrows():
                for _ in range(int(row["Adet"])):
                    all_pieces.append({"w": row["En (cm)"], "h": row["Boy (cm)"]})
            
            # Akıllı Döndürme
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
                    new_plate = {"shelves": [], "y_used": 0, "items": [], "waste": []}
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
                        st.error(f"❌ Hata: {w}x{h} ölçüsü ana plakadan büyük!")
                        st.stop()
            
            # Fire (Kalan Boşluk) Hesaplama
            for plate in plates:
                for shelf in plate["shelves"]:
                    waste_w = round(L_w - shelf["x_used"], 1)
                    if waste_w > 0:
                        plate["waste"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": waste_w, "h": shelf["height"]})
                waste_h = round(L_h - plate["y_used"], 1)
                if waste_h > 0:
                    plate["waste"].append({"x": 0, "y": plate["y_used"], "w": L_w, "h": waste_h})

            st.success(f"✅ Cam Kesim Haritası Hazır! Toplam Plaka: {len(plates)} Adet")
            st.info("💡 BİLGİ: Seçtiğin camı döndürmek için üstteki 🔄 butonuna bas. Sürüklerken diğer camlara veya köşelere mıknatıs gibi yapışacaktır!")
            
            # İNTERAKTİF HTML MIKNATISLI EKRAN
            for idx, plate in enumerate(plates):
                st.subheader(f"🔍 Plaka {idx+1}")
                
                html_code = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <style>
                  body {{ margin: 0; padding: 0; font-family: sans-serif; overflow: hidden; }}
                  .toolbar {{
                      background-color: #f1faee; border: 2px solid #a8dadc; border-radius: 5px;
                      padding: 10px; margin-bottom: 10px; text-align: center;
                  }}
                  .rotate-btn {{
                      background-color: #1d3557; color: white; border: none; border-radius: 5px;
                      padding: 10px 20px; font-size: 16px; font-weight: bold; cursor: pointer;
                      box-shadow: 2px 2px 5px rgba(0,0,0,0.3); transition: 0.2s;
                  }}
                  .rotate-btn:hover {{ background-color: #457b9d; transform: scale(1.05); }}
                  .rotate-btn:active {{ transform: scale(0.95); }}
                  .plate-wrapper {{
                      position: relative; width: 100%; padding-bottom: {(L_h / L_w) * 100}%;
                      background-color: #2b2b2b; border: 3px solid #1e1e1e; box-sizing: border-box;
                      touch-action: none; overflow: hidden;
                  }}
                  .piece {{
                      position: absolute; background-color: rgba(42, 157, 143, 0.9);
                      border: 1px solid #fff; display: flex; align-items: center; justify-content: center;
                      color: white; font-weight: bold; font-size: 14px; text-align: center; line-height: 1.2;
                      cursor: grab; user-select: none; box-sizing: border-box; transition: box-shadow 0.2s;
                  }}
                  .piece.selected {{ box-shadow: 0px 0px 15px 5px #e63946; z-index: 999; border: 2px solid #fff; }}
                  .piece:active {{ cursor: grabbing; }}
                  
                  .waste {{
                      position: absolute; background: repeating-linear-gradient(45deg, #444, #444 10px, #555 10px, #555 20px);
                      border: 2px dashed #888; display: flex; align-items: center; justify-content: center;
                      color: #ccc; font-weight: bold; font-size: 12px; text-align: center; line-height: 1.2;
                      box-sizing: border-box; pointer-events: none; opacity: 0.7; z-index: 0;
                  }}
                  
                  @media (max-width: 600px) {{ .piece, .waste {{ font-size: 10px; }} }}
                </style>
                </head>
                <body>
                
                <div class="toolbar">
                    <button class="rotate-btn" onclick="rotateSelected()">🔄 Seçili Camı Döndür (90°)</button>
                    <span style="display:block; font-size:12px; color:#333; margin-top:5px;">(Döndürmek için plakadaki camın üstüne bir kez tıkla ve seç, sonra bu tuşa bas)</span>
                </div>

                <div class="plate-wrapper" id="plate" data-pw="{L_w}" data-ph="{L_h}">
                """
                
                # FİRELERİ ÇİZİM
                for w_item in plate.get("waste", []):
                    left_pct = (w_item["x"] / L_w) * 100
                    top_pct = (w_item["y"] / L_h) * 100
                    w_pct = (w_item["w"] / L_w) * 100
                    h_pct = (w_item["h"] / L_h) * 100
                    html_code += f'<div class="waste" style="left:{left_pct}%; top:{top_pct}%; width:{w_pct}%; height:{h_pct}%;">FİRE<br>↔ {w_item["w"]}<br>↕ {w_item["h"]}</div>'

                # CAMLARI ÇİZİM
                for item in plate["items"]:
                    left_pct = (item["x"] / L_w) * 100
                    top_pct = (item["y"] / L_h) * 100
                    w_pct = (item["w"] / L_w) * 100
                    h_pct = (item["h"] / L_h) * 100
                    html_code += f'<div class="piece" style="left:{left_pct}%; top:{top_pct}%; width:{w_pct}%; height:{h_pct}%;" data-w="{item["w"]}" data-h="{item["h"]}" onclick="selectPiece(this)">↔ {item["w"]}<br>↕ {item["h"]}</div>'
                
                html_code += """
                </div>
                <script>
                  let dragged = null;
                  let selected = null;
                  let startX, startY, startLeft, startTop;

                  function selectPiece(el) {
                      if (selected) { selected.classList.remove('selected'); }
                      selected = el;
                      selected.classList.add('selected');
                  }

                  function rotateSelected() {
                      if (!selected) { alert("Lütfen önce tablodan döndürmek istediğiniz cama tıklayarak seçin!"); return; }
                      
                      let plateW = parseFloat(document.getElementById('plate').getAttribute('data-pw'));
                      let plateH = parseFloat(document.getElementById('plate').getAttribute('data-ph'));
                      
                      let oldW = parseFloat(selected.getAttribute('data-w'));
                      let oldH = parseFloat(selected.getAttribute('data-h'));
                      
                      let newW = oldH;
                      let newH = oldW;
                      
                      let newW_pct = (newW / plateW) * 100;
                      let newH_pct = (newH / plateH) * 100;
                      
                      let currentLeft = parseFloat(selected.style.left) || 0;
                      let currentTop = parseFloat(selected.style.top) || 0;
                      
                      // Plakadan dışarı taşıyorsa içeri it
                      if (currentLeft + newW_pct > 100) currentLeft = 100 - newW_pct;
                      if (currentTop + newH_pct > 100) currentTop = 100 - newH_pct;
                      
                      selected.setAttribute('data-w', newW);
                      selected.setAttribute('data-h', newH);
                      selected.style.width = newW_pct + "%";
                      selected.style.height = newH_pct + "%";
                      selected.style.left = currentLeft + "%";
                      selected.style.top = currentTop + "%";
                      selected.innerHTML = "↔ " + newW + "<br>↕ " + newH;
                  }

                  function startDrag(e) {
                      if(!e.target.classList.contains('piece')) return;
                      selectPiece(e.target);
                      dragged = e.target;
                      let clientX = e.touches ? e.touches[0].clientX : e.clientX;
                      let clientY = e.touches ? e.touches[0].clientY : e.clientY;
                      startX = clientX;
                      startY = clientY;
                      startLeft = parseFloat(dragged.style.left) || 0;
                      startTop = parseFloat(dragged.style.top) || 0;
                      dragged.style.zIndex = 1000;
                  }

                  function drag(e) {
                      if (!dragged) return;
                      e.preventDefault(); 
                      let clientX = e.touches ? e.touches[0].clientX : e.clientX;
                      let clientY = e.touches ? e.touches[0].clientY : e.clientY;
                      let dx = clientX - startX;
                      let dy = clientY - startY;

                      let parentRect = dragged.parentElement.getBoundingClientRect();
                      let dxPercent = (dx / parentRect.width) * 100;
                      let dyPercent = (dy / parentRect.height) * 100;

                      let newLeft = startLeft + dxPercent;
                      let newTop = startTop + dyPercent;
                      
                      let wPercent = parseFloat(dragged.style.width);
                      let hPercent = parseFloat(dragged.style.height);

                      // --- SNAP (MIKNATIS) SİSTEMİ ---
                      let snapThreshold = 1.5; // %1.5 yakınlaşınca yapışır
                      let pieces = document.querySelectorAll('.piece');
                      let newRight = newLeft + wPercent;
                      let newBottom = newTop + hPercent;
                      
                      // 1. Kenarlara Yapışma
                      if (newLeft < snapThreshold) newLeft = 0;
                      if (newTop < snapThreshold) newTop = 0;
                      if (100 - newRight < snapThreshold) newLeft = 100 - wPercent;
                      if (100 - newBottom < snapThreshold) newTop = 100 - hPercent;

                      // 2. Diğer Camlara Yapışma
                      pieces.forEach(p => {
                          if(p === dragged) return;
                          let pLeft = parseFloat(p.style.left);
                          let pTop = parseFloat(p.style.top);
                          let pRight = pLeft + parseFloat(p.style.width);
                          let pBottom = pTop + parseFloat(p.style.height);

                          // Yatay Mıknatıs
                          if (Math.abs(newLeft - pRight) < snapThreshold) newLeft = pRight;
                          if (Math.abs(newRight - pLeft) < snapThreshold) newLeft = pLeft - wPercent;
                          if (Math.abs(newLeft - pLeft) < snapThreshold) newLeft = pLeft;

                          // Dikey Mıknatıs
                          if (Math.abs(newTop - pBottom) < snapThreshold) newTop = pBottom;
                          if (Math.abs(newBottom - pTop) < snapThreshold) newTop = pTop - hPercent;
                          if (Math.abs(newTop - pTop) < snapThreshold) newTop = pTop;
                      });

                      dragged.style.left = newLeft + '%';
                      dragged.style.top = newTop + '%';
                  }

                  function endDrag(e) {
                      if (dragged) {
                          dragged.style.zIndex = '';
                          dragged = null;
                      }
                  }

                  document.addEventListener('mousedown', startDrag);
                  document.addEventListener('mousemove', drag);
                  document.addEventListener('mouseup', endDrag);

                  document.addEventListener('touchstart', startDrag, {passive: false});
                  document.addEventListener('touchmove', drag, {passive: false});
                  document.addEventListener('touchend', endDrag);
                </script>
                </body>
                </html>
                """
                
                estimated_height = int(700 * (L_h / L_w)) + 80
                components.html(html_code, height=estimated_height)
