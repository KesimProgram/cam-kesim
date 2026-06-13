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
st.set_page_config(page_title="Cam Kesim Optimizasyonu", layout="wide")
st.title("🔮 Cam Kesim & Görsel Yerleşim Masası")

if 'df_cam' not in st.session_state:
    st.session_state.df_cam = pd.DataFrame({"En (cm)": [0.0], "Boy (cm)": [0.0], "Adet": [0]})

# --- AYARLAR ---
with st.sidebar:
    st.header("⚙️ Plaka Ayarları")
    st.info("Cam kesiminde testere payı yoktur (Elmas payı sıfır kabul edilir).")
    L_w = st.number_input("Ana Plaka Genişliği / En (cm)", value=321.0, step=1.0)
    L_h = st.number_input("Ana Plaka Yüksekliği / Boy (cm)", value=225.0, step=1.0)
    
    st.divider()
    rotation_aktif = st.checkbox("Camları Döndürmeye İzin Ver (90°)", value=True)
    
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
if st.button("🚀 Haritayı Çiz & Düzenlemeye Başla", type="primary"):
    df_temiz = df_giris[(df_giris["En (cm)"] > 0) & (df_giris["Boy (cm)"] > 0) & (df_giris["Adet"] > 0)].copy()
    
    if df_temiz.empty:
        st.warning("Lütfen geçerli cam ölçüleri girin.")
    else:
        with st.spinner("Camlar plakaya diziliyor..."):
            all_pieces = []
            for _, row in df_temiz.iterrows():
                for _ in range(int(row["Adet"])):
                    all_pieces.append({"w": row["En (cm)"], "h": row["Boy (cm)"], "label": f"{row['En (cm)']}x{row['Boy (cm)']}"})
            
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
                            plate["items"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": w, "h": h, "label": piece["label"]})
                            shelf["x_used"] += w
                            placed = True; break
                        elif rotation_aktif and shelf["x_used"] + h <= L_w and w <= shelf["height"]:
                            plate["items"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": h, "h": w, "label": piece["label"]})
                            shelf["x_used"] += h
                            placed = True; break
                    if placed: break
                    
                    if plate["y_used"] + h <= L_h and w <= L_w:
                        new_shelf = {"y_start": plate["y_used"], "height": h, "x_used": w}
                        plate["items"].append({"x": 0, "y": plate["y_used"], "w": w, "h": h, "label": piece["label"]})
                        plate["shelves"].append(new_shelf)
                        plate["y_used"] += h
                        placed = True; break
                    elif rotation_aktif and plate["y_used"] + w <= L_h and h <= L_w:
                        new_shelf = {"y_start": plate["y_used"], "height": w, "x_used": h}
                        plate["items"].append({"x": 0, "y": plate["y_used"], "w": h, "h": w, "label": piece["label"]})
                        plate["shelves"].append(new_shelf)
                        plate["y_used"] += w
                        placed = True; break
                
                if not placed:
                    new_plate = {"shelves": [], "y_used": 0, "items": []}
                    if w <= L_w and h <= L_h:
                        new_shelf = {"y_start": 0, "height": h, "x_used": w}
                        new_plate["items"].append({"x": 0, "y": 0, "w": w, "h": h, "label": piece["label"]})
                        new_plate["shelves"].append(new_shelf)
                        new_plate["y_used"] += h
                        plates.append(new_plate)
                    elif rotation_aktif and h <= L_w and w <= L_h:
                        new_shelf = {"y_start": 0, "height": w, "x_used": h}
                        new_plate["items"].append({"x": 0, "y": 0, "w": h, "h": w, "label": piece["label"]})
                        new_plate["shelves"].append(new_shelf)
                        new_plate["y_used"] += w
                        plates.append(new_plate)
                    else:
                        st.error(f"❌ Hata: {piece['label']} ölçüsü {L_w}x{L_h} ana plakadan büyük!")
                        st.stop()
            
            st.success(f"✅ Cam Kesim Haritası Hazır! Toplam Plaka: {len(plates)} Adet")
            st.info("💡 BİLGİ: Aşağıdaki haritada cam parçalarının üzerine tıklayıp parmağınla (veya fareyle) sürükleyerek elmasla daha rahat keseceğin hizada yeniden düzenleyebilirsin!")
            
            # İNTERAKTİF SÜRÜKLE-BIRAK (DRAG & DROP) EKRANI
            for idx, plate in enumerate(plates):
                st.subheader(f"🔍 Plaka {idx+1}")
                
                # HTML/CSS/JS ile Sürükle Bırak Motoru
                html_code = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <style>
                  body {{ margin: 0; padding: 0; font-family: sans-serif; background: transparent; }}
                  .plate-wrapper {{
                      position: relative;
                      width: 100%;
                      padding-bottom: {(L_h / L_w) * 100}%; /* Orantıyı korur */
                      background-color: #2b2b2b;
                      border: 3px solid #1e1e1e;
                      border-radius: 4px;
                      touch-action: none; /* Mobilde kaydırmayı engeller */
                      overflow: hidden;
                  }}
                  .piece {{
                      position: absolute;
                      background-color: rgba(42, 157, 143, 0.85);
                      border: 1px solid #fff;
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      color: white;
                      font-weight: bold;
                      font-size: 14px;
                      cursor: grab;
                      user-select: none;
                      box-sizing: border-box;
                      box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
                      transition: background-color 0.1s;
                  }}
                  .piece:active {{ cursor: grabbing; }}
                  /* Çok küçük parçalarda yazıyı küçült */
                  @media (max-width: 500px) {{ .piece {{ font-size: 10px; }} }}
                </style>
                </head>
                <body>
                <div class="plate-wrapper" id="plate">
                """
                
                # Parçaları Yüzdelik Oranlarla Ekleme (Telefona tam otursun diye)
                for item in plate["items"]:
                    left_pct = (item["x"] / L_w) * 100
                    top_pct = (item["y"] / L_h) * 100
                    w_pct = (item["w"] / L_w) * 100
                    h_pct = (item["h"] / L_h) * 100
                    
                    html_code += f'<div class="piece" style="left:{left_pct}%; top:{top_pct}%; width:{w_pct}%; height:{h_pct}%;">{item["label"]}</div>'
                
                html_code += """
                </div>
                <script>
                  let dragged = null;
                  let startX, startY, startLeft, startTop;

                  function startDrag(e) {
                      if(e.target.className !== 'piece') return;
                      dragged = e.target;
                      let clientX = e.touches ? e.touches[0].clientX : e.clientX;
                      let clientY = e.touches ? e.touches[0].clientY : e.clientY;
                      startX = clientX;
                      startY = clientY;
                      startLeft = parseFloat(dragged.style.left) || 0;
                      startTop = parseFloat(dragged.style.top) || 0;
                      dragged.style.zIndex = 1000;
                      dragged.style.backgroundColor = "rgba(231, 111, 81, 0.9)"; // Tutunca turuncu olur
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

                      // Plakadan dışarı taşmayı engelle
                      let wPercent = parseFloat(dragged.style.width);
                      let hPercent = parseFloat(dragged.style.height);
                      if(newLeft < 0) newLeft = 0;
                      if(newTop < 0) newTop = 0;
                      if(newLeft + wPercent > 100) newLeft = 100 - wPercent;
                      if(newTop + hPercent > 100) newTop = 100 - hPercent;

                      dragged.style.left = newLeft + '%';
                      dragged.style.top = newTop + '%';
                  }

                  function endDrag(e) {
                      if (dragged) {
                          dragged.style.zIndex = 1;
                          dragged.style.backgroundColor = "rgba(42, 157, 143, 0.85)"; // Bırakınca yeşile döner
                          dragged = null;
                      }
                  }

                  // Mouse Eventleri (Bilgisayar İçin)
                  document.addEventListener('mousedown', startDrag);
                  document.addEventListener('mousemove', drag);
                  document.addEventListener('mouseup', endDrag);

                  // Dokunmatik Eventleri (Telefon/Tablet İçin)
                  document.addEventListener('touchstart', startDrag, {passive: false});
                  document.addEventListener('touchmove', drag, {passive: false});
                  document.addEventListener('touchend', endDrag);
                </script>
                </body>
                </html>
                """
                
                # Iframe yüksekliğini plaka oranına göre tahmini olarak hesaplama
                estimated_height = int(700 * (L_h / L_w))
                components.html(html_code, height=estimated_height + 20)
