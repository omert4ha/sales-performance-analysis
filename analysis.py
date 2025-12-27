import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Excel dosyalarını yükle
df_alıs = pd.read_excel("alış 2 aylıkk.xlsx")
df_satıs = pd.read_excel("satışş.xlsx")

# Tarih ve saat sütunlarını dönüştür
df_alıs["Fatura Tarihi"] = pd.to_datetime(df_alıs["Fatura Tarihi"])
df_alıs["Fatura Saati"] = pd.to_datetime(df_alıs["Fatura Saati"], format="%H:%M:%S", errors="coerce").dt.time
df_alıs["İptal"] = df_alıs["İptal"].str.lower().str.strip()
df_alıs = df_alıs[df_alıs["İptal"] != "evet"]

df_satıs["Fatura Tarihi"] = pd.to_datetime(df_satıs["Fatura Tarihi"], errors='coerce')
df_satıs["İptal"] = df_satıs["İptal"].str.lower().str.strip()
df_satıs = df_satıs[df_satıs["İptal"] != "evet"]

# Ortak sütunları birleştir
common_cols = ["Fatura Tarihi", "Genel Toplam", "Pazarlama Personeli", "Cari Kodu", "Ticari Unvanı", "İli","İlçesi"]
df_combined = pd.concat([
    df_alıs[common_cols],
    df_satıs[common_cols]
], ignore_index=True)

# Eksik personel isimlerini doldur
df_combined["Pazarlama Personeli"].fillna("Bilinmiyor", inplace=True)

# Gün ve saat bilgisi ekle
df_combined["Gün"] = df_combined["Fatura Tarihi"].dt.day_name()
df_combined["Saat"] = df_combined["Fatura Tarihi"].dt.hour




# Toplam satış sayısı ve tutarı
personel_satis_sayisi = df_combined["Pazarlama Personeli"].value_counts()
personel_toplam_tutar = df_combined.groupby("Pazarlama Personeli")["Genel Toplam"].sum()
personel_ortalama = df_combined.groupby("Pazarlama Personeli")["Genel Toplam"].mean()

# Gün bazlı satış adedi
zaman_gun = df_combined.groupby(["Pazarlama Personeli", "Gün"]).size().unstack().fillna(0)

# Bar grafiği - Toplam satış tutarı
plt.figure(figsize=(10, 6))
sns.barplot(x=personel_toplam_tutar.sort_values(ascending=False).values,
            y=personel_toplam_tutar.sort_values(ascending=False).index)
plt.title("Personel Bazlı Toplam Satış Tutarı")
plt.xlabel("Toplam Satış Tutarı")
plt.ylabel("Pazarlama Personeli")
plt.tight_layout()
plt.show()

# Zaman çizelgesi - Gün bazlı satış aktivitesi
plt.figure(figsize=(12, 6))
zaman_gun.T.plot(kind='line', marker='o')
plt.title("Personel Performansı (Gün Bazlı Satış Adedi)")
plt.xlabel("Gün")
plt.ylabel("Satış Sayısı")
plt.legend(title="Pazarlama Personeli")
plt.grid(True)
plt.tight_layout()
plt.show()




# En çok alışveriş yapan (fatura sayısına göre)
en_cok_alisveris = df_combined["Ticari Unvanı"].value_counts().head(10)

# En çok harcayan müşteriler
en_cok_harcayan = df_combined.groupby("Ticari Unvanı")["Genel Toplam"].sum().sort_values(ascending=False).head(10)

# Ortalama müşteri harcaması
ortalama_harcama = df_combined.groupby("Ticari Unvanı")["Genel Toplam"].mean()

# Pasta grafiği - En çok alışveriş yapan müşteriler
plt.figure(figsize=(10, 6))
plt.pie(en_cok_alisveris.values, labels=en_cok_alisveris.index, autopct="%1.1f%%", startangle=140)
plt.title("En Çok Alışveriş Yapan Müşteri Dağılımı (İlk 10)")
plt.tight_layout()
plt.show()

# Bar grafiği - En çok harcayan müşteriler
plt.figure(figsize=(10, 6))
sns.barplot(x=en_cok_harcayan.values, y=en_cok_harcayan.index)
plt.title("En Çok Harcayan Müşteriler (İlk 10)")
plt.xlabel("Toplam Harcama")
plt.ylabel("Ticari Unvan")
plt.tight_layout()
plt.show()

# Histogram - Ortalama müşteri harcaması
plt.figure(figsize=(10, 6))
sns.histplot(ortalama_harcama, bins=20, kde=True)
plt.title("Müşteri Başına Ortalama Harcama Dağılımı")
plt.xlabel("Ortalama Harcama")
plt.ylabel("Müşteri Sayısı")
plt.tight_layout()
plt.show()





from datetime import datetime

# Analiz tarihi: veri setindeki en son tarihten 1 gün sonrası
referans_tarih = df_combined["Fatura Tarihi"].max() + pd.Timedelta(days=1)

# RFM tabloları
rfm = df_combined.groupby("Ticari Unvanı").agg({
    "Fatura Tarihi": lambda x: (referans_tarih - x.max()).days,  # Recency
    "Cari Kodu": "count",                                        # Frequency
    "Genel Toplam": "sum"                                        # Monetary
})

rfm.columns = ["Recency", "Frequency", "Monetary"]

# Segmentlere ayırma: skor ver
rfm["R_Score"] = pd.qcut(rfm["Recency"], 4, labels=[4, 3, 2, 1])
rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4])
rfm["M_Score"] = pd.qcut(rfm["Monetary"], 4, labels=[1, 2, 3, 4])

# RFM skorlarını birleştir
rfm["RFM_Score"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)

# Segmentleme: örnek eşiklere göre
def segment_kategori(rfm_score):
    if rfm_score == "444":
        return "Sadık Müşteri"
    elif rfm_score[0] == "4":
        return "Yeni Müşteri"
    elif rfm_score[1] == "4":
        return "Sık Alışveriş Yapan"
    elif rfm_score[2] == "4":
        return "Çok Harcayan"
    else:
        return "Riskli Müşteri"

rfm["Segment"] = rfm["RFM_Score"].apply(segment_kategori)

# Segment dağılımı
print(rfm["Segment"].value_counts())

# Pie chart
plt.figure(figsize=(8, 6))
rfm["Segment"].value_counts().plot.pie(autopct="%1.1f%%", startangle=140)
plt.title("Müşteri Segment Dağılımı")
plt.ylabel("")
plt.tight_layout()
plt.show()




import geopandas as gpd
import pandas as pd
import os
import matplotlib.pyplot as plt

# Şehir dosyalarının bulunduğu klasör
klasor_yolu = os.path.join(os.getcwd(), "cities")

# Tüm JSON dosyalarını oku ve birleştir
geo_list = []
for dosya in os.listdir(klasor_yolu):
    if dosya.endswith(".json"):
        tam_yol = os.path.join(klasor_yolu, dosya)
        try:
            gdf = gpd.read_file(tam_yol)
            geo_list.append(gdf)
        except Exception as e:
            print(f"Hata: {dosya} - {e}")

# Tüm şehirlerin geometrilerini tek bir GeoDataFrame'de birleştir
turkey_map = pd.concat(geo_list, ignore_index=True)

# İllere göre satış verisi
sehir_satis = df_combined.groupby("İli")["Genel Toplam"].sum().reset_index()
sehir_satis.columns = ["name", "satis"]

# Eşleştirme için büyük harfe çevir
sehir_satis["name"] = sehir_satis["name"].str.upper().str.strip()
turkey_map["name"] = turkey_map["name"].str.upper().str.strip()

# Harita ile satışları birleştir
map_merged = turkey_map.merge(sehir_satis, on="name", how="left")
map_merged["satis"] = map_merged["satis"].fillna(0)

# Haritayı çiz
plt.figure(figsize=(14, 10))
map_merged.plot(column="satis", cmap="YlOrRd", linewidth=0.5, edgecolor="0.8", legend=True)
plt.title("Türkiye İllere Göre Satış Tutarı", fontsize=16)
plt.axis("off")
plt.show()









# Alış ve satış toplamlarını il bazında gruplama
alis_il = df_alıs.groupby("İli")["Genel Toplam"].sum().reset_index()
alis_il.columns = ["Il", "Alis"]

satis_il = df_satıs.groupby("İli")["Genel Toplam"].sum().reset_index()
satis_il.columns = ["Il", "Satis"]

# Büyük harfe çevir ve temizle
alis_il["Il"] = alis_il["Il"].str.upper().str.strip()
satis_il["Il"] = satis_il["Il"].str.upper().str.strip()

# Alış ve satışları birleştir
kar_hesap = pd.merge(alis_il, satis_il, on="Il", how="outer").fillna(0)

# Kar ve kar marjı hesapla
kar_hesap["Kar"] = kar_hesap["Satis"] - kar_hesap["Alis"]
kar_hesap["Kar_Marji"] = kar_hesap["Kar"] / kar_hesap["Alis"]
kar_hesap["Kar_Marji"] = kar_hesap["Kar_Marji"].replace([float('inf'), -float('inf')], 0)  # Sonsuzları 0 yap

print(kar_hesap)


import geopandas as gpd
import matplotlib.pyplot as plt

# city_map: şehir geometrilerini içeren GeoDataFrame
# kar_hesap: il bazında kar ve kar marjı içeren DataFrame

# Büyük harfe çevir ve temizle (harita verisindeki isimler)
turkey_map["name"] = turkey_map["name"].str.upper().str.strip()
kar_hesap["Il"] = kar_hesap["Il"].str.upper().str.strip()

# Merge işlemi
map_merged = turkey_map.merge(kar_hesap, left_on="name", right_on="Il", how="left")
map_merged["Kar_Marji"] = map_merged["Kar_Marji"].fillna(0)

# Haritayı çiz (kar marjı üzerinden)
plt.figure(figsize=(14, 10))
map_merged.plot(column="Kar_Marji", cmap="YlGnBu", linewidth=0.8, edgecolor="0.8", legend=True,
                legend_kwds={'label': "Kar Marjı", 'orientation': "horizontal"})

plt.title("Türkiye İllere Göre Kar Marjı Haritası", fontsize=16)
plt.axis("off")
plt.show()



import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(16, 7))
kar_hesap["Kar_Marji_%"] = kar_hesap["Kar_Marji"] * 100

# Sıralı barplot (en yüksek kar marjından en düşüğe)
sns.barplot(data=kar_hesap.sort_values("Kar_Marji", ascending=False),
            x="Il", y="Kar_Marji_%", palette="coolwarm")

plt.xticks(rotation=90)
plt.ylabel("Kar Marjı (%)")
plt.xlabel("İl")
plt.title("İllere Göre Kar Marjı (%)")
plt.tight_layout()
plt.show()






# Satış verisi zaten df_satıs içinde var, iptal olmayanlar filtrelenmişti
# Personel bazında toplam ve ortalama satış
personel_perf = df_satıs.groupby("Pazarlama Personeli")["Genel Toplam"].agg(["sum", "mean", "count"]).reset_index()
personel_perf.columns = ["Personel", "Toplam Satış", "Ortalama Satış", "Satış Sayısı"]

# Satışları büyükten küçüğe sırala
personel_perf = personel_perf.sort_values("Toplam Satış", ascending=False)

print(personel_perf)


# Günlük toplam satışları personel bazında grupla
df_satıs["Fatura Tarihi"] = pd.to_datetime(df_satıs["Fatura Tarihi"])

daily_sales = df_satıs.groupby(["Pazarlama Personeli", "Fatura Tarihi"])["Genel Toplam"].sum().reset_index()

# Örnek olarak ilk 5 personelin günlük satış trendini çizelim
top_personeller = personel_perf["Personel"].head(5).tolist()

import matplotlib.pyplot as plt

plt.figure(figsize=(15,8))
for personel in top_personeller:
    temp = daily_sales[daily_sales["Pazarlama Personeli"] == personel]
    plt.plot(temp["Fatura Tarihi"], temp["Genel Toplam"], label=personel)

plt.title("Top 5 Pazarlama Personelinin Günlük Satış Trendleri")
plt.xlabel("Tarih")
plt.ylabel("Günlük Satış Tutarı")
plt.legend()
plt.show()







