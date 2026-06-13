import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import json
import os

# --- KAYIT SİSTEMİ FONKSİYONLARI ---
def kayitlari_yukle(dosya_adi):
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def kayit_ekle(dosya_adi, isim, data):
    kayitlar = kayitlari_yukle(dosya_adi)
    kayitlar[isim] = data
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(kayitlar, f, ensure_ascii=False, indent=4)

def kayit_sil(dosya_adi, isim):
    kayitlar = kayitlari_yukle(dosya_adi)
    if isim in kayitlar:
        del kayitlar[isim]
        with open(dosya_adi, "w", encoding="utf-8") as f:
            json.dump(kayitlar, f, ensure_ascii=False, indent=4)

# --- SAYFA GENEL AYARLARI ---
st.set_page_config(page_title="Atölye Kesim Optimizasyonu", layout="wide")
st.title("🏭 Reis Atölye Kesim Merkezi")

# Sekmeleri Oluşturuyoruz
tab1, tab2 = st.tabs(["✂️ Profil Kesim Dünyası", "🔮 Cam Kesim Dünyası"])

# ==============================================================================
# ======================== SEKME 1: PROFİL KESİM ===============================
# ==============================================================================
with tab1:
    st.header("✂️ Profil Kesim Optimizasyonu")
    
    # Profil Ayarları (Direkt ekrana alındı, telefon için kolaylık)
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        L_input = st.number_input("Profil Uzunluğu (cm)", value=600.0, step=1.0, key="p_L")
        testere = st.number_input("Testere Payı (cm)", value=0.5, step=0.1, key="p_t")
    with col_p2:
        kural_aktif = st.checkbox("5 cm - 30 cm Kuralını Uygula", value=True, key="p_k")
        if kural_aktif:
            min_fire = st.number_input("Çöp Fire Üst Sınırı (cm)", value=5.0, key="p_min")
            max_fire = st.number_input("Kullanılabilir Fire Alt Sınırı (cm)", value=30.0, key="p_max")
        else:
            min_fire, max_fire = 0.0, 0.0

    st.write("---")
    
    # Hafıza ve Sipariş Tablosu
    if 'df_profil' not in st.session_state:
        st.session_state.df_profil = pd.DataFrame({"Boy (cm)": [0.0], "Adet": [0]})
        
    st.subheader("📋 Profil Sipariş Listesi")
    df_profil_giris = st.data_editor(st.session_state.df_profil, num_rows="dynamic", use_container_width=True, key="editor_profil")
    st.session_state.df_profil = df_profil_giris

    # Profil Kayıt Bölümü
    col_pk1, col_pk2 = st.columns([3, 1])
    with col_pk1:
        p_kayit_ismi = st.text_input("Bu profil listesine isim ver:", key="p_name")
    with col_pk2:
        st.write(" ") 
        st.write(" ")
        if st.button("💾 Profili Kaydet", use_container_width=True, key="p_save_btn"):
            if p_kayit_ismi:
                df_gecerli = df_profil_giris[(df_profil_giris["Boy (cm)"] > 0) & (df_profil_giris["Adet"] > 0)]
                kayit_ekle("kayitlar_profil.json", p_kayit_ismi, df_gecerli.to_dict('records'))
                st.success("Profil listesi kaydedildi!")
                st.rerun()

    # Profil Yükleme/Silme
    p_kayitlar = kayitlari_yukle("kayitlar_profil.json")
    if p_kayitlar:
        st.write("📂 **Kayıtlı Profiller:**")
        col_pl1, col_pl2 = st.columns([3, 1])
        with col_pl1:
            p_secilen = st.selectbox("Yüklenecek İşi Seç:", ["Seçiniz..."] + list(p_kayitlar.keys()), key="p_sel")
        with col_pl2:
            st.write(" ")
            col_p_sub1, col_p_sub2 = st.columns(2)
            with col_p_sub1:
                if st.button("📂 Yükle", key="p_load_btn") and p_secilen != "Seçiniz...":
                    st.session_state.df_profil = pd.DataFrame(p_kayitlar[p_secilen])
                    st.rerun()
            with col_p_sub2:
                if st.button("🗑️ Sil", key="p_del_btn") and p_secilen != "Seçiniz...":
                    kayit_sil("kayitlar_profil.json", p_secilen)
                    st.rerun()

    # HESAPLAMA MOTORU (PROFİL)
    if st.button("🚀 Profil Optimizasyonunu Başlat", type="primary", key="p_start"):
        df_temiz = df_profil_giris[(df_profil_giris["Boy (cm)"] > 0) & (df_profil_giris["Adet"] > 0)].copy()
        if df_temiz.empty:
            st.warning("Lütfen geçerli ölçü girin.")
        else:
            with st.spinner("Hesaplanıyor..."):
                uzunluklar = df_temiz["Boy (cm)"].tolist()
                gercek_uzunluklar = [boy + testere for boy in uzunluklar]
                adetler = df_temiz["Adet"].tolist()
                L = L_input
                Gecerli_Desenler = []
                
                def desen_uret(index, mevcut_desen, mevcut_uzunluk):
                    if index == len(gercek_uzunluklar):
                        fire = L - mevcut_uzunluk
                        if fire >= 0:
                            if kural_aktif:
                                if fire <= (min_fire + 0.05) or fire >= (max_fire - 0.05): Gecerli_Desenler.append(tuple(mevcut_desen))
                            else: Gecerli_Desenler.append(tuple(mevcut_desen))
                        return
                    max_adet = int((L - mevcut_uzunluk) // gercek_uzunluklar[index])
                    for i in range(max_adet + 1):
                        mevcut_desen.append(i)
                        desen_uret(index + 1, mevcut_desen, mevcut_uzunluk + i * gercek_uzunluklar[index])
                        mevcut_desen.pop()

                desen_uret(0, [], 0.0)
                if not Gecerli_Desenler:
                    st.error("Uygun kesim ihtimali bulunamadı.")
                else:
                    A_eq = np.array(Gecerli_Desenler).T
                    b_eq = np.array(adetler)
                    c = np.ones(len(Gecerli_Desenler))
                    constraints_tam = LinearConstraint(A_eq, b_eq, b_eq)
                    res = milp(c=c, constraints=constraints_tam, integrality=np.ones_like(c), bounds=Bounds(0, np.inf), options={'time_limit': 60})
                    
                    cozum_gecerli = False
                    if res.success or (hasattr(res, 'x') and res.x is not None):
                        cozum_gecerli = True
                        cozum = np.round(res.x).astype(int)
                    else:
                        res_esnek = milp(c=c, constraints=LinearConstraint(A_eq, b_eq, np.inf), integrality=np.ones_like(c), bounds=Bounds(0, np.inf))
                        if res_esnek.success:
                            cozum_gecerli = True
                            cozum = np.round(res_esnek.x).astype(int)
                    
                    if cozum_gecerli:
                        kalan_ihtiyac = {uzunluklar[i]: adetler[i] for i in range(len(uzunluklar))}
                        kesim_listesi = []
                        for i, miktar in enumerate(cozum):
                            if miktar > 0:
                                for _ in range(miktar):
                                    profil_kesim, kullanilan_boy = {}, 0
                                    for j, parca_adeti in enumerate(Gecerli_Desenler[i]):
                                        boy = uzunluklar[j]
                                        kesilecek = min(parca_adeti, kalan_ihtiyac[boy])
                                        if kesilecek > 0:
                                            profil_kesim[boy] = kesilecek
                                            kullanilan_boy += kesilecek * gercek_uzunluklar[j]
                                            kalan_ihtiyac[boy] -= kesilecek
                                    if profil_kesim:
                                        kesim_listesi.append({'kesimler': tuple(profil_kesim.items()), 'fire': round(L - kullanilan_boy, 1)})
                        
                        st.success(f"✅ Toplam Profil: {len(kesim_listesi)} Adet")
                        profil_no = 1
                        grup_dict = {}
                        for p in kesim_listesi:
                            key = (p['kesimler'], p['fire'])
                            if key not in grup_dict: grup_dict[key] = []
                            grup_dict[key].append(profil_no)
                            profil_no += 1
                            
                        for key, nolar in grup_dict.items():
                            kesimler, fire = key
                            str_baslik = f"**Profil {nolar[0]}**" if len(nolar)==1 else f"**Profil {nolar[0]} - {nolar[-1]} arası** ({len(nolar)} Adet)"
                            detay = " | ".join([f"{adet} adet {boy} cm" for boy, adet in kesimler])
                            durum = "♻️ Sağlam" if fire >= max_fire else ("🗑️ Çöp" if fire <= min_fire else "⚠️ Mecburi")
                            st.markdown(f"- {str_baslik}: 👉 {detay} *(Fire: {fire} cm - {durum})*")

# ==============================================================================
# ========================== SEKME 2: CAM KESİM ================================
# ==============================================================================
with tab2:
    st.header("🔮 Görsel Çizimli Cam Kesim Optimizasyonu")
    
    # Cam Plaka Ayarları
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        L_w = st.number_input("Plaka Genişliği / En (cm)", value=321.0, step=1.0, key="c_w")
    with col_c2:
        L_h = st.number_input("Plaka Yükseklikleri / Boy (cm)", value=225.0, step=1.0, key="c_h")
    with col_c3:
        testere_cam = st.number_input("Elmas / Kesim Payı (cm)", value=0.2, step=0.1, key="c_t")
        rotation_aktif = st.checkbox("Camları Döndürmeye İzin Ver (90 derece)", value=True, key="c_r")

    st.write("---")
    
    if 'df_cam' not in st.session_state:
        st.session_state.df_cam = pd.DataFrame({"En (cm)": [0.0], "Boy (cm)": [0.0], "Adet": [0]})
        
    st.subheader("📋 Cam Kesim Sipariş Listesi")
    df_cam_giris = st.data_editor(st.session_state.df_cam, num_rows="dynamic", use_container_width=True, key="editor_cam")
    st.session_state.df_cam = df_cam_giris

    # Cam Kayıt Bölümü
    col_ck1, col_ck2 = st.columns([3, 1])
    with col_ck1:
        c_kayit_ismi = st.text_input("Bu cam işine isim ver (Örn: Cam Kapak):", key="c_name")
    with col_ck2:
        st.write(" ") 
        st.write(" ")
        if st.button("💾 Camı Kaydet", use_container_width=True, key="c_save_btn"):
            if c_kayit_ismi:
                df_gecerli_cam = df_cam_giris[(df_cam_giris["En (cm)"] > 0) & (df_cam_giris["Boy (cm)"] > 0) & (df_cam_giris["Adet"] > 0)]
                kayit_ekle("kayitlar_cam.json", c_kayit_ismi, df_gecerli_cam.to_dict('records'))
                st.success("Cam sipariş listesi kaydedildi!")
                st.rerun()

    # Cam Yükleme/Silme
    c_kayitlar = kayitlari_yukle("kayitlar_cam.json")
    if c_kayitlar:
        st.write("📂 **Kayıtlı Cam İşleri:**")
        col_cl1, col_cl2 = st.columns([3, 1])
        with col_cl1:
            c_secilen = st.selectbox("Yüklenecek Cam İşini Seç:", ["Seçiniz..."] + list(c_kayitlar.keys()), key="c_sel")
        with col_cl2:
            st.write(" ")
            col_c_sub1, col_c_sub2 = st.columns(2)
            with col_c_sub1:
                if st.button("📂 Yükle", key="c_load_btn") and c_secilen != "Seçiniz...":
                    st.session_state.df_cam = pd.DataFrame(c_kayitlar[c_secilen])
                    st.rerun()
            with col_c_sub2:
                if st.button("🗑️ Sil", key="c_del_btn") and c_secilen != "Seçiniz...":
                    kayit_sil("kayitlar_cam.json", c_secilen)
                    st.rerun()

    # HESAPLAMA MOTORU VE GÖRSEL ÇİZİCİ (2D SHELF PACKER)
    if st.button("🚀 Cam Optimizasyonunu ve Şemayı Başlat", type="primary", key="c_start"):
        df_cam_temiz = df_cam_giris[(df_cam_giris["En (cm)"] > 0) & (df_cam_giris["Boy (cm)"] > 0) & (df_cam_giris["Adet"] > 0)].copy()
        
        if df_cam_temiz.empty:
            st.warning("Lütfen geçerli cam ölçüleri girin.")
        else:
            with st.spinner("Camlar plakaya diziliyor, kesim haritası çiziliyor..."):
                all_pieces = []
                for _, row in df_cam_temiz.iterrows():
                    for _ in range(int(row["Adet"])):
                        all_pieces.append({"w": row["En (cm)"], "h": row["Boy (cm)"], "label": f"{row['En (cm)']}x{row['Boy (cm)']}"})
                
                # Akıllı Ön-Döndürme Ayarı
                if rotation_aktif:
                    for p in all_pieces:
                        if p["w"] < p["h"]: p["w"], p["h"] = p["h"], p["w"]
                
                # Yüksekliğe göre büyükten küçüğe sırala (Raf algoritması)
                all_pieces.sort(key=lambda x: x["h"], reverse=True)
                
                plates = []
                for piece in all_pieces:
                    w, h = piece["w"], piece["h"]
                    placed = False
                    
                    for plate in plates:
                        for shelf in plate["shelves"]:
                            if shelf["x_used"] + w <= L_w and h <= shelf["height"]:
                                plate["items"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": w, "h": h, "label": piece["label"]})
                                shelf["x_used"] += w + testere_cam
                                placed = True; break
                            elif rotation_aktif and shelf["x_used"] + h <= L_w and w <= shelf["height"]:
                                plate["items"].append({"x": shelf["x_used"], "y": shelf["y_start"], "w": h, "h": w, "label": piece["label"]})
                                shelf["x_used"] += h + testere_cam
                                placed = True; break
                        if placed: break
                        
                        if plate["y_used"] + h <= L_h and w <= L_w:
                            new_shelf = {"y_start": plate["y_used"], "height": h, "x_used": w + testere_cam}
                            plate["items"].append({"x": 0, "y": plate["y_used"], "w": w, "h": h, "label": piece["label"]})
                            plate["shelves"].append(new_shelf)
                            plate["y_used"] += h + testere_cam
                            placed = True; break
                        elif rotation_aktif and plate["y_used"] + w <= L_h and h <= L_w:
                            new_shelf = {"y_start": plate["y_used"], "height": w, "x_used": h + testere_cam}
                            plate["items"].append({"x": 0, "y": plate["y_used"], "w": h, "h": w, "label": piece["label"]})
                            plate["shelves"].append(new_shelf)
                            plate["y_used"] += w + testere_cam
                            placed = True; break
                    
                    if not placed:
                        new_plate = {"shelves": [], "y_used": 0, "items": []}
                        if w <= L_w and h <= L_h:
                            new_shelf = {"y_start": 0, "height": h, "x_used": w + testere_cam}
                            new_plate["items"].append({"x": 0, "y": 0, "w": w, "h": h, "label": piece["label"]})
                            new_plate["shelves"].append(new_shelf)
                            new_plate["y_used"] += h + testere_cam
                            plates.append(new_plate)
                        elif rotation_aktif and h <= L_w and w <= L_h:
                            new_shelf = {"y_start": 0, "height": w, "x_used": h + testere_cam}
                            new_plate["items"].append({"x": 0, "y": 0, "w": h, "h": w, "label": piece["label"]})
                            new_plate["shelves"].append(new_shelf)
                            new_plate["y_used"] += w + testere_cam
                            plates.append(new_plate)
                        else:
                            st.error(f"❌ Hata: {piece['label']} ölçüsü ana plakadan büyük!")
                            st.stop()
                
                st.success(f"✅ Cam Kesim Haritası Hazır! Toplam Gerekli Plaka: {len(plates)} Adet")
                
                # GÖRSEL ŞEMALARI SVG İLE ÇİZME BÖLÜMÜ
                colors = ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#6d597a", "#355070", "#b56576"]
                for idx, plate in enumerate(plates):
                    st.subheader(f"🔮 Plaka {idx+1} Kesim Şeması")
                    
                    # Dinamik yükseklik ayarı (Orantı bozulmasın diye)
                    svg_height = max(250, min(550, int(700 * (L_h / L_w))))
                    
                    svg = f'<svg width="100%" height="{svg_height}" viewBox="0 0 {L_w} {L_h}" xmlns="http://www.w3.org/2000/svg" style="border:3px solid #1e1e1e; background:#e0e0e0; border-radius:8px;">'
                    
                    for item in plate["items"]:
                        c_idx = sum(ord(c) for c in item["label"]) % len(colors)
                        color = colors[c_idx]
                        
                        # Cam dikdörtgeni
                        svg += f'<rect x="{item["x"]}" y="{item["y"]}" width="{item["w"]}" height="{item["h"]}" fill="{color}" stroke="#ffffff" stroke-width="0.8" rx="2" ry="2"/>'
                        
                        # Ölçü yazısı
                        f_size = max(5, min(14, int(min(item["w"], item["h"]) / 4)))
                        svg += f'<text x="{item["x"] + item["w"]/2}" y="{item["y"] + item["h"]/2}" font-size="{f_size}" fill="#ffffff" font-family="sans-serif" font-weight="bold" text-anchor="middle" dominant-baseline="middle">{item["label"]}</text>'
                    
                    svg += '</svg>'
                    st.markdown(svg, unsafe_allow_html=True)
                    st.caption(f"Yukarıdaki şema {L_w}x{L_h} cm boyutundaki plakanın birebir yerleşim haritasıdır.")
