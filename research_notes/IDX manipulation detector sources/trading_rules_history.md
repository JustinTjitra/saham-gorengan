# IDX (BEI) trading rules that affect how daily price and volume data must be read, 2015 to November 2026

How these notes were made, and how far to trust them:
- This research ran on 2026-11-20. WebFetch was blocked for the hosts tried (market.bisnis.com, snips.stockbit.com: "host not in allowed network domains"), so no article or idx.co.id PDF was opened in full. Every finding below comes from **search-engine result extracts** of the cited articles. The extracts sometimes quote the article directly. They are still secondary summaries, not the primary decree text.
- Labels used: **[V-multi]** means several independent outlets agree in the extracts. **[V-single]** means one outlet only. **[INF]** means my own inference. **[UNCHECKED]** means a value already in the repo, or from background knowledge, that this pass did not re-verify.
- None of the decrees (Kep-xxxxx/BEI) were read on idx.co.id. Before treating any number as final, open the decree PDFs under "Peraturan > Perdagangan" or "Berita > Pengumuman" on idx.co.id.

## 1. Is the April 2025 asymmetric ARB 15% still in force in November 2026?

### Takeaway
**No.** The April 2025 regime (ARB 15%, Rp50 floor) lasted until 2026-09-25. Two further changes have followed:
- **2026-09-28** (Kep-00136/BEI/09-2026): the minimum price dropped from Rp50 to Rp1, and a new Rp1–Rp10 tier was added with a fixed Rp1 limit in both directions. ARB stayed at 15% for prices above Rp10.
- **2026-10-19** (Kep-00157/BEI/10-2026): ARB was cut to 7% for prices above Rp10, after the MSCI-driven crash and trading halt on 2026-10-16.
- **2026-10-20** (Kep-00158/BEI/10-2026): this refined the 7% rule. The ARB for the Rp11–Rp14 band became a fixed Rp1.

The current regime runs "until 2026-12-31, then to be evaluated". A return to symmetric limits from 2027-01-01 had been announced in September 2026, but the October cut has made that plan uncertain.

### Cited findings
**The April 2025 regime (verifying the repo's R2025-ARB15 row)**
- On 2025-04-08 IDX cut ARB to 15% for all price tiers on the Main, Development and New Economy boards, under Kep-00003/BEI/04-2025 dated 2025-04-08 (an amendment to Peraturan II-A). Kep-00002/BEI/04-2025 (trading continuity in emergency conditions) was issued alongside it. [V-multi] — [Hukumonline](https://www.hukumonline.com/berita/a/bei-lakukan-penyesuaian-aturan-perdagangan-efek-lt67f4abb2a449a?page=all); [Kontan/MomsMoney](https://momsmoney.kontan.co.id/news/bei-tetapkan-auto-rejection-bawah-arb-hanya-15-dan-mengubah-batas-trading-halt-8); [Warta Ekonomi](https://wartaekonomi.co.id/read563019/bei-ubah-aturan-perdagangan-naikkan-batas-trading-halt-jadi-8-dan-pangkas-batas-arb-jadi-15); [Bareksa](https://www.bareksa.com/berita/saham/2025-04-08/aturan-baru-bei-soal-trading-halt-berlaku-mulai-8-april-2025-ihsg-bisa-stop-seharian)
- OJK letter S-101/D.04/2025, dated 2025-09-17, postponed short selling. Reports say the same letter also covered trading halts and auto-rejection limits, which is consistent with the April 2025 measures being kept in place. [V-single] — [Investortrust](https://investortrust.id/market/80174/implementasi-short-selling-ditunda-lagi-hingga-2026-alasan-ini-diungkap-bei)

**Change 1: minimum price Rp1 and a new Rp1–Rp10 tier, effective Monday 2026-09-28**
- The minimum price on the regular and cash markets was cut from Rp50 to Rp1. The legal basis is two decrees dated 2026-09-21: Kep-00136/BEI/09-2026 (equity securities) and Kep-00137/BEI/09-2026 (DINFRA). One outlet writes the second number as "Kep-000137". The start date was first targeted for 2026-09-07 and then postponed, and member-firm trials were held on 2026-08-22 and 2026-08-29. [V-multi] — [Media Indonesia](https://mediaindonesia.com/ekonomi/936319/bei-ubah-batas-auto-rejection-dan-harga-minimum-saham-rp1-per-28-september-2026); [Kontan](https://investasi.kontan.co.id/news/mengenal-kebijakan-baru-bei-soal-harga-minimum-saham-rp1-beserta-batas-ara-arb); [Bloomberg Technoz](https://www.bloombergtechnoz.com/detail-news/122260/bei-turunkan-minimum-harga-saham-jadi-rp1-auto-rejection-berubah); [Investortrust (trial)](https://investortrust.id/market/113578/bei-ubah-batas-minimum-harga-saham-jadi-rp1-uji-coba-mulai-22-agustus-2026)
- The new limits by price band:

  | Price band | ARA | ARB |
  |---|---|---|
  | Rp1–Rp10 | Rp1 (nominal) | Rp1 (nominal) |
  | >Rp10–200 | 35% | 15% |
  | >Rp200–5,000 | 25% | 15% |
  | >Rp5,000 | 20% | 15% |

  ARB stays asymmetric at 15% for prices above Rp10 during a transition from 2026-09-28 to 2026-12-31. The "full" scheme was described as starting on 2027-01-01. [V-multi] — [Kabar SDGs](https://kabarsdgs.com/sustainability/2026/09/28382/bei-turunkan-batas-harga-minimum-saham-jadi-rp1/); [Pentradr](https://www.pentradr.com/2026/09/bei-berlakukan-harga-minimum-saham-rp1.html); [Ajaib](https://ajaib.co.id/belajar/berita/aturan-baru-ara-arb-saham-28-september-2026); [PintarSaham](https://pintarsaham.id/bei-sesuaikan-batasan-harga-terendah-minimum-dan-batasan-auto-rejection-efek-bersifat-ekuitas-dan-dinfra-di-pasar-reguler-dan-pasar-tunai/)
- Stockbit's headline: "BEI Ubah Klasifikasi Auto Rejection per 28 September 2026, ARB Simetris per 2027". Investor.id: "Siap-siap, BEI Terapkan ARB Simetris". [V-multi, headline level] — [Stockbit Snips](https://snips.stockbit.com/snips-terbaru/-bei-ubah-klasifikasi-auto-rejection-per-28-september-2026-arb-simetris-per-2027); [Investor.id](https://investor.id/market/454910/siapsiap-bei-terapkan-arb-simetris)
- On the first day, 26 stocks that had been stuck at Rp50 fell below Rp50 in session I. [V-single] — [Bisnis](https://market.bisnis.com/read/20260928/7/2007761/era-saham-rp1-dimulai-26-saham-eks-gocap-berguguran-sesi-i)

**Change 2: ARB 7%, effective Monday 2026-10-19**
- Kep-00157/BEI/10-2026 cut ARB from 15% to 7% for all price bands above Rp10. ARA was unchanged, and the Rp1–Rp10 band kept its Rp1 limit. The decree replaced the corresponding provision of Kep-00136/BEI/09-2026. It runs from 2026-10-19 to 2026-12-31 and will then be evaluated. Trading-halt rules were not changed: IDX President Director Jeffrey Hendrik said only the ARB provision was adjusted. [V-multi] — [CNBC Indonesia](https://www.cnbcindonesia.com/market/20261019062711-17-777291/bei-terapkan-batas-auto-rejection-bawah-jadi-7-mulai-hari-ini); [Bisnis](https://market.bisnis.com/read/20261019/7/2013651/bei-pangkas-batas-auto-rejection-bawah-arb-jadi-asimetris-7); [Kontan](https://investasi.kontan.co.id/news/mengenal-arti-arb-7-yang-mulai-dijalankan-bei-per-19-oktober-2026); [Republika](https://ekonomi.republika.co.id/berita/tn4kd5370/jaga-stabilitas-pasar-bei-sesuaikan-aturan-auto-reject-bawah-saham-jadi-7-persen); [Periskop (halt unchanged)](https://periskop.id/pasar-modal/20261019/arb-7-persen-trading-halt-jeffrey-hendrik); [Maybank Trade](https://www.maybanktrade.co.id/berita/arb-saham-jadi-7-mulai-hari-ini-hingga-akhir-2026/)
- The trigger was the IHSG falling about 8% at the open on 2026-10-16 (a trading halt). The cause was MSCI's consultation on reclassifying Indonesia from Emerging Market to Standalone Market. [V-multi] — [CNBC Indonesia research](https://www.cnbcindonesia.com/research/20261016095125-128-776739/perdagangan-bursa-sempat-alami-trading-halt-ini-aturan-sejarahnya); [Periskop](https://periskop.id/pasar-modal/20261016/trading-halt-ihsg-tiga-kali-pada-2026-msci-kembali-guncang-bursa)

**Change 3: Rp11–Rp14 band ARB becomes Rp1, effective Tuesday 2026-10-20**
- Kep-00158/BEI/10-2026 sets the ARB for prices of Rp11–Rp14 at a nominal Rp1, replacing 7%. ARA in that band stays at 35%. It runs from 2026-10-20 to 2026-12-31. The full schedule:

  | Price band | ARA | ARB |
  |---|---|---|
  | Rp1–10 | Rp1 | Rp1 |
  | Rp11–14 | 35% | Rp1 |
  | Rp15–200 | 35% | 7% |
  | >Rp200–5,000 | 25% | 7% |
  | >Rp5,000 | 20% | 7% |

  It applies to the Main, Development and New Economy boards. The Acceleration Board and the Papan Pemantauan Khusus keep their own limits. [V-multi] — [Media Indonesia](https://mediaindonesia.com/ekonomi/946380/bei-sesuaikan-batas-arb-saham-berharga-rp11rp14-menjadi-rp1); [Republika](https://ekonomi.republika.co.id/berita/tn6s16370/bursa-efek-indonesia-perbarui-ketentuan-auto-reject-bawah-untuk-saham-harga-rendah); [Suara](https://www.suara.com/bisnis/2026/10/20/090650/bei-rombak-lagi-aturan-arb-harga-saham-rp11-dan-rp14-bisa-jadi-rp1); [Warta Ekonomi](https://wartaekonomi.co.id/read642124/bei-ubah-lagi-aturan-arb-saham-rp11rp14-kini-dibatasi-jadi-rp1); [Ajaib](https://ajaib.co.id/belajar/berita/bei-ubah-lagi-aturan-arb-saham-harga-rp11-rp14-kini-turun-maksimal-rp1)
- **Conflict on the decree number:** most extracts write the replaced decree as "Kep-000157/BEI/10-2026" (six digits). Others write "Kep-00157/BEI/10-2026". IDX's usual format is five digits, so Kep-00157 is probably correct. [INF]

**Checking the repo's earlier rows (partial)**
- 13 March 2020: Kep-00025/BEI/03-2020, dated 2020-03-12, cut ARB from 10% to 7% for all tiers, effective 2020-03-13. It followed an OJK order dated 2020-03-12 (S-273/PM.21/2020 is cited). [V-multi] — [Pasardana](https://pasardana.id/news/2020/3/12/bei-sesuaikan-ketentuan-auto-rejection-dan-saham-yang-diperdagangkan-pada-sesi-pra-pembukaan); [CNN Indonesia](https://www.cnnindonesia.com/ekonomi/20200313074512-92-483053/bursa-saham-tertekan-batas-auto-rejection-jadi-7-persen). This matches the repo's choice of Kep-00025. The repo's note that Kompas cites Kep-00024 is still an open conflict. **Correction:** the repo's R2020-ARB10 row also cites S-273/PM.21/2020 as the OJK order behind the 10 March change. The extract here ties S-273 to the **12 March** order (the 7% change), so check that row.
- Bisnis wrote on 2022-12-28 that the pandemic-era trading hours and the asymmetric ARB were "still in force". This is consistent with R2020-ARB7 lasting into 2023. [V-single] — [Bisnis](https://market.bisnis.com/read/20221228/7/1612953/bei-tegaskan-jam-perdagangan-saat-pandemi-dan-arb-asimetris-masih-berlaku)
- R2015-ASYM (2015-08-24, Kep-00096/BEI/08-2015), R2017-SYM (2017-01-03, Kep-00113/BEI/12-2016), R2020-ARB10 (2020-03-10, Kep-00023/BEI/03-2020) and the 2023 dates (2023-06-05 and 2023-09-04, under Kep-00055/BEI/03-2023): [UNCHECKED] in this pass. One extract confirms that limits moved to a new scheme on 2017-01-03 ([Pasardana 2020](https://pasardana.id/news/2020/3/12/bei-sesuaikan-ketentuan-auto-rejection-dan-saham-yang-diperdagangkan-pada-sesi-pra-pembukaan)).

### Inferences
- **Suggested replacement for the CSV's last regime.** All four regimes below cover the Main, Development and New Economy boards. "X / Y" means ARA / ARB; a figure without % is a nominal rupiah limit.

  | Regime | Dates | Rp1–10 | Rp11–14 | Rp15–200 | >Rp200–5,000 | >Rp5,000 | Decree |
  |---|---|---|---|---|---|---|---|
  | R2025-ARB15 | 2025-04-08 to 2026-09-25 | n/a (Rp50 floor) | 35% / 15% | 35% / 15% | 25% / 15% | 20% / 15% | Kep-00003/BEI/04-2025 |
  | R2026-RP1-ARB15 | 2026-09-28 to 2026-10-16 | Rp1 / Rp1 | 35% / 15% | 35% / 15% | 25% / 15% | 20% / 15% | Kep-00136/BEI/09-2026 |
  | R2026-ARB7 | 2026-10-19 only (one trading day) | Rp1 / Rp1 | 35% / 7% | 35% / 7% | 25% / 7% | 20% / 7% | Kep-00157/BEI/10-2026 |
  | R2026-ARB7-B | 2026-10-20 to 2026-12-31 (scheduled) | Rp1 / Rp1 | 35% / Rp1 | 35% / 7% | 25% / 7% | 20% / 7% | Kep-00158/BEI/10-2026 |

  In R2025-ARB15 the Rp11–14 and Rp15–200 columns are one tier: Rp50–200. 2026-09-26 and 2026-09-27 were a weekend, and so were 2026-10-17 and 2026-10-18.
- The CSV schema needs a way to hold **nominal (Rp) limits** alongside percentages, for example `ara_abs` and `arb_abs` columns or a `limit_type` column. Its lowest tier must change from "0–200" to "10–200" from 2026-09-28 onward.
- **Why the Rp11–14 fix was needed:** 7% of Rp14 is Rp0.98, which is smaller than the Rp1 tick, so a stock priced at Rp11–14 could not fall at all under a pure 7% rule. Kep-00158 fixes that edge case. This is my reading of the arithmetic. No source states it.
- **Rp50 floor effect for a detector:** until 2026-09-25, stocks on the regular boards could not trade below Rp50 ("gocap"). Rows stuck at Rp50 with no downside are floor-censored, not stable. From 2026-09-28 that censoring disappears. A burst of new lows in ex-gocap stocks that week reflects the rule change, not manipulation.
- The 2027-01-01 "symmetric" plan was announced before the October 7% cut. Whether it still holds after the 2026-12-31 review is unknown. Model 2027 as unknown until IDX announces something.

### Gaps
- None of the 2026 decree PDFs (Kep-00136, Kep-00137, Kep-00157, Kep-00158) were read directly. Whether ARA or ARB is measured as "more than Rp1" or "Rp1 or more" from the reference price was not verified in the decree text.
- No source found says whether the 2026-09-28 or 2026-10-19 changes altered the IPO first-day limits.
- No IDX statement after 2026-10-20 about 2027 was found.

## 2. Acceleration Board and Papan Pemantauan Khusus / full call auction (FCA) limits

### Takeaway
**Acceleration Board** (launched 2019): minimum price Rp1. The limit is Rp1 for prices of Rp1–Rp10 and 10% above Rp10, in both directions. A December 2020 decree (Kep-00109/BEI/12-2020) is reported to have kept the 10% figure.

**Papan Pemantauan Khusus with FCA** (stage II, from 2024-03-25): minimum price Rp1. The limit is Rp1 for prices of Rp1–Rp10 and 10% above Rp10. IDX proposed a tiered 35/25/20% scheme for FCA stocks in July 2026, but it is not confirmed as adopted. Separately, 92 stocks were moved out of FCA on 2026-09-28. All 2025–2026 regular-board ARB changes explicitly exclude both of these boards.

### Cited findings
- **Acceleration Board, design (May 2019):** minimum price Rp1, against Rp50 on the Main and Development boards. The limit is Rp1 for prices of Rp1–10 and 10% above Rp10. [V-single, pre-launch statement by Trading Director Laksono Widodo] — [Pasardana 2019-05-28](https://pasardana.id/news/2019/5/28/papan-akselerasi-mungkinkan-investor-beli-saham-rp-1/); also [Kontan](https://investasi.kontan.co.id/news/bei-merilis-aturan-perdagangan-saham-pada-papan-akselerasi), [Detik](https://finance.detik.com/bursa-dan-valas/d-4737045/bei-persempit-aksi-goreng-saham-di-papan-perdagangan-startup)
- Kep-00109/BEI/12-2020 kept the 10% limit above Rp10 for the Acceleration Board, as reported by CNBC Indonesia. In April 2021, two newly listed Acceleration Board stocks fell by more than the "normal" ARB. [V-single, via search extract] — [CNBC Indonesia 2021-04-16](https://www.cnbcindonesia.com/market/20210416141902-17-238464/2-emiten-baru-sahamnya-drop-di-bawah-arb-normal-kok-bisa)
- The Kep-00158 coverage in October 2026 states that the Acceleration Board and the Papan Pemantauan Khusus "still follow their own board-specific auto-rejection rules". [V-multi] — [Republika](https://ekonomi.republika.co.id/berita/tn6s16370/bursa-efek-indonesia-perbarui-ketentuan-auto-reject-bawah-untuk-saham-harga-rendah); [Ajaib](https://ajaib.co.id/belajar/berita/bei-ubah-lagi-aturan-arb-saham-harga-rp11-rp14-kini-turun-maksimal-rp1). The April 2025 ARB 15% likewise named only the Main, Development and New Economy boards ([Hukumonline](https://www.hukumonline.com/berita/a/bei-lakukan-penyesuaian-aturan-perdagangan-efek-lt67f4abb2a449a?page=all)).
- **Papan Pemantauan Khusus:**
  - In January 2023 IDX explained that the planned board would allow ARB down to Rp1. [V-single] — [Bisnis 2023-01-27](https://market.bisnis.com/read/20230127/7/1622280/arb-bisa-rp1-di-papan-pemantauan-khusus-bursa-beri-penjelasan)
  - The board launched on 2023-06-12 (stage I). [V-multi, headline level] — [Bisnis 2023-06-12](https://market.bisnis.com/read/20230612/7/1664714/papan-pemantauan-khusus-bei-meluncur-investor-bisa-lebih-aman)
  - Stage II, with full call auction, started on 2024-03-25. It allows prices down to Rp1. The limit is Rp1 for Rp1–Rp10 and 10% above Rp10. There are 5 call sessions a day Monday to Thursday and 4 on Friday. The order book does not show bids or asks, only IEP and IEV (indicative equilibrium price and volume). [V-multi] — [Bisnis 2024-03-15](https://market.bisnis.com/read/20240315/7/1749731/bei-terapkan-papan-pemantauan-khusus-full-call-auction-25-maret); [Bisnis 2024-03-25](https://market.bisnis.com/read/20240325/7/1752586/bei-luncurkan-papan-pemantauan-khusus-tahap-ii-cek-detailnya); [Kontan Insight](https://insight.kontan.co.id/news/simak-skema-baru-perdagangan-full-call-auction-di-papan-pemantauan-khusus); [Warta Ekonomi](https://wartaekonomi.co.id/read531629/bei-akan-terapkan-papan-pemantauan-khusus-full-call-auction-pada-25-maret-2024)
  - Example: BREN hit a 10% ARB on 2024-05-29 after being placed on the FCA board. [V-single] — [Bisnis](https://market.bisnis.com/read/20240529/7/1769261/saham-bren-prajogo-pangestu-langsung-arb-10-akibat-ppk-full-call-auction)
- **2026 FCA revision:**
  - In July 2026 IDX proposed removing three FCA criteria. [V-multi] — [Kompas 2026-07-05](https://money.kompas.com/read/2026/07/05/082323126/bei-bakal-ubah-aturan-papan-pemantauan-khusus-3-kriteria-dihapus); [Suara](https://www.suara.com/bisnis/2026/07/03/142735/isu-bei-bakal-rombak-total-aturan-fca-3-kriteria-ini-bakal-dihapus)
  - It also proposed tiered FCA limits for prices above Rp10: 35% for Rp10–200, 25% for Rp200–5,000 and 20% above Rp5,000. [V-multi, proposal only] — [Bisnis 2026-07-06](https://market.bisnis.com/read/20260706/7/1985764/bei-siapkan-aturan-baru-auto-rejection-untuk-saham-fca); [Periskop](https://periskop.id/saham/20260706/bei-auto-rejection-saham-fca-ppk); [Kontan Insight (critical)](https://insight.kontan.co.id/news/revisi-ppk-bei-auto-rejection-hingga-35-membuat-risiko-investor-ritel-kian-besar)
  - 92 issuers were removed from the FCA board effective 2026-09-28 because criteria 1, 6, 7 and 10 no longer applied. This happened at the same time as the removal of the Rp50 floor. [V-multi] — [Maybank Trade](https://www.maybanktrade.co.id/berita/92-emiten-keluar-dari-fca-bei-mulai-28-september-2026/); [Investor.id](https://investor.id/market/455591/92-emiten-keluar-papan-pemantauan-khusus-fca); [Katadata](https://katadata.co.id/finansial/bursa/6ab88bb98f54a/bei-keluarkan-92-saham-dari-fca-picu-volatilitas-saat-harga-bawah-rp-1-berlaku)
- **Conflict:** Pintu (undated blog) still describes the FCA limit as 10% above Rp10. No extract confirmed that the tiered 35/25/20% FCA scheme took effect. [V-single] — [Pintu](https://pintu.co.id/blog/fca-saham-adalah)

### Inferences
- From 2024-03-25 onward, encode FCA days as a separate regime: Rp1 nominal for Rp1–10 and ±10% above Rp10. That remains the default unless the 35/25/20% proposal is confirmed. FCA closing prices come from periodic call auctions, so daily OHLC and volume patterns differ structurally from continuous-trading stocks. Volume is lumpy and the intraday range is narrow.
- Acceleration Board: encode Rp1 nominal for Rp1–10 and ±10% above Rp10 from the 2019 launch. [INF; the exact launch date was not verified in this pass]
- The 2026-09-28 mass exit of 92 stocks from FCA back to continuous trading is a structural break for those tickers.

### Gaps
- The Acceleration Board launch decree number and exact launch date (2019) were not verified.
- The detail of Papan Pemantauan Khusus stage I (2023-06-12) was not established: whether it used continuous trading with a notation, or FCA.
- Any 2024–2025 "hybrid" FCA revision and its effective date were not found.
- The status of the 35/25/20% FCA proposal is unknown.

## 3. IPO first-day auto-rejection limits

### Takeaway
Before 2020-03-13, first-day IPO limits were **2× the normal percentage**. Kep-00025/BEI/03-2020 cut them to **1×** from 2020-03-13. No later change was found.

### Cited findings
- Kep-00025/BEI/03-2020 (dated 2020-03-12, effective 2020-03-13) cut the first-day ("perdagangan perdana") auto-rejection limit from 2× the normal percentage to 1×. The extract notes that sources disagree slightly on how the earlier 2× rule was worded. [V-multi] — [Pasardana](https://pasardana.id/news/2020/3/12/bei-sesuaikan-ketentuan-auto-rejection-dan-saham-yang-diperdagangkan-pada-sesi-pra-pembukaan); [CNN Indonesia](https://www.cnnindonesia.com/ekonomi/20200313074512-92-483053/bursa-saham-tertekan-batas-auto-rejection-jadi-7-persen)

### Inferences
- Under 1×, a first-day IPO is bounded by the regime's ARA and ARB, measured from the offer price. For example, a Rp100 IPO could close at most at Rp135 in 2020–2026. Whether the 1× rule survived each later regime (2023, 2025, 2026) is assumed, not verified. [INF]

### Gaps
- No source was found for the IPO-day rule after 2023, or for how the 2026 nominal Rp1 tiers apply to IPOs.

## 4. Tick size (fraksi harga) history

### Takeaway
There have been three price-band groups since 2014-01-06: under Rp500 at Rp1, Rp500 to under Rp5,000 at Rp5, and Rp5,000 and above at Rp25. From **2016-05-02** (Kep-00023/BEI/04-2016) there are five groups. These were found unchanged through 2023. No 2021, 2023 or 2024 tick change was found.

### Cited findings
- Kep-00023/BEI/04-2016 set five tick groups, effective 2016-05-02:

  | Price band | Tick | Max change per order |
  |---|---|---|
  | Under Rp200 | Rp1 | Rp10 |
  | Rp200 to under Rp500 | Rp2 | Rp20 |
  | Rp500 to under Rp2,000 | Rp5 | Rp50 |
  | Rp2,000 to under Rp5,000 | Rp10 | Rp100 |
  | Rp5,000 and above | Rp25 | Rp250 |

  [V-multi] — [Bisnis 2016-05-02](https://market.bisnis.com/read/20160502/190/543637/bei-berlakukan-fraksi-harga-baru-mulai-hari-ini-simak-rincian-perubahannya); [CNN Indonesia 2016-05-23](https://www.cnnindonesia.com/ekonomi/20160523135607-78-132774/bei-sebut-penambahan-fraksi-harga-dongkrak-transaksi-saham/); [Kontan (proposal)](https://investasi.kontan.co.id/news/bei-usulkan-lima-fraksi-harga-saham)
- The previous three-group scheme was: under Rp500 at Rp1, Rp500 to under Rp5,000 at Rp5, and Rp5,000 and above at Rp25. Bisnis reported the January 2014 change. [V-single for the dating] — [Bisnis 2014-01-06](https://market.bisnis.com/read/20140106/191/195655/kamus-bursa-bei-ubah-fraksi-harga-ini-definisinya)
- An OCBC explainer from February 2023 still lists the same five groups. [V-single] — [OCBC](https://www.ocbc.id/id/article/2023/02/16/fraksi-harga-saham-adalah)

### Inferences
- The project brief mentions "changes in 2016 and 2023/2024". I found **no evidence** of a tick change in 2023 or 2024. The 2016 change was on **2016-05-02**, not in January 2016. With the Rp1 floor from 2026-09-28, the Rp1 tick now applies down to Rp1, so a one-tick move at Rp2 is 50%.

### Gaps
- Whether the 2026 Rp1 floor decree changed any tick band was not confirmed.
- Whether the "max change per order" rule is still in force was not confirmed.

## 5. Lot size

### Takeaway
1 lot = 100 shares since January 2014, down from 500. No later change was found. [UNCHECKED in this pass]

### Cited findings
- The January 2014 tick and lot reform is referenced in [Bisnis 2014-01-06](https://market.bisnis.com/read/20140106/191/195655/kamus-bursa-bei-ubah-fraksi-harga-ini-definisinya) and [Bisnis 2013-08-18](https://market.bisnis.com/read/20130818/190/157399/perubahan-fraksi-harga-saham-picu-pro-dan-kontra-bei-perlu-kaji-lagi). The extracts confirm a tick and lot change around 2014-01-06, with conflicting mentions of 2013-12-01. [V-single]

### Gaps
- None of the extracts states the 500→100 figure explicitly. That figure rests on background knowledge. No change was found between 2015 and 2026.

## 6. Trading hours, sessions and the opening and closing call auctions

### Takeaway
The changes that matter for closing-price analysis:
- **COVID hours from 2020-03-30**, still in force at end-2022.
- **Pre-opening suspended from 2020-03-13**, then restored for LQ45 stocks only from 2020-09-07.
- **From 2021-12-06**: IEP and IEV published during pre-opening and pre-closing, random closing between 14:58 and 15:00, and broker codes hidden in real-time post-trade data.
- **Pre-opening and pre-closing extended to more stocks in December 2024.**
- **Non-cancellation period from December 2025**: pre-closing orders cannot be amended from 15:56.

### Cited findings
- The trading and reporting schedule was adjusted from 2020-03-30, following shorter BI-RTGS hours and work-from-home policy. [V-single] — [Bisnis 2020-03-30](https://market.bisnis.com/read/20200330/7/1219446/ingat-mulai-hari-ini-jadwal-perdagangan-dan-pelaporan-bursa-disesuaikan)
- From 2020-03-13, stocks were removed from the pre-opening session until further notice. [V-single] — [Pasardana](https://pasardana.id/news/2020/3/12/bei-sesuaikan-ketentuan-auto-rejection-dan-saham-yang-diperdagangkan-pada-sesi-pra-pembukaan)
- Pre-opening resumed for LQ45 constituents from 2020-09-07. [V-single] — [Bisnis 2020-09-06](https://market.bisnis.com/read/20200906/7/1287822/ingat-sesi-pre-opening-indeks-lq45-mulai-berlaku-besok-7-september-2020)
- The pandemic-era trading hours were still in force on 2022-12-28. [V-single] — [Bisnis](https://market.bisnis.com/read/20221228/7/1612953/bei-tegaskan-jam-perdagangan-saat-pandemi-dan-arb-asimetris-masih-berlaku); [Katadata (new guideline, hours may normalise)](https://katadata.co.id/finansial/bursa/63abeb2c80fa6/bei-rilis-pedoman-baru-jam-perdagangan-akan-kembali-normal)
- From 2021-12-06: IEP and IEV were shown in pre-opening and pre-closing, a random closing time was introduced (14:58–15:00 during the pandemic schedule), and broker codes were closed in real-time post-trade data. [V-multi] — [Bisnis 2021-12-06](https://market.bisnis.com/read/20211206/7/1474334/mekanisme-pre-closing-dan-penutupan-kode-broker-resmi-berlaku-hari-ini); [Bisnis 2021-11-24](https://market.bisnis.com/read/20211124/7/1469927/dear-investor-begini-perubahan-mekanisme-pre-closing-dan-penutupan-kode-broker)
- In December 2024 the list of stocks eligible for pre-opening and pre-closing was extended beyond LQ45. Pre-closing at that time ran 15:50:00–16:00:59. [V-multi] — [Bisnis 2024-12-03](https://market.bisnis.com/read/20241203/7/1821024/ini-daftar-saham-yang-kini-bisa-ditransaksikan-di-sesi-pra-opening); [IDX Channel](https://www.idxchannel.com/market-news/mulai-pekan-depan-bei-resmi-perluas-saham-pre-opening-dan-pre-closing/all)
- From December 2025, a non-cancellation period applies: pre-closing orders cannot be amended or cancelled from 15:56 WIB. [V-single] — [Bareksa 2025-12-11](https://www.bareksa.com/berita/saham/2025-12-11/jangan-salah-input-bei-terapkan-aturan-baru-order-saham-kini-dikunci-di-jam-tertentu/amp)
- The current schedule as commonly quoted is in the table below. Sources differ on the end of pre-closing (15:59, 16:00 or 16:00:59) and on the start of post-trading (16:01 or 16:02). [V-multi, inconsistent seconds] — [MetroTV](https://www.metrotvnews.com/read/k8oCVlZe-ini-detail-jam-kerja-bursa-saham); [Ajaib](https://ajaib.co.id/belajar/pemula/jam-bursa-saham-indonesia)

  | Session | Monday–Thursday | Friday |
  |---|---|---|
  | Pre-opening | 08:45–08:59 | 08:45–08:59 |
  | Session I | 09:00–12:00 | 09:00–11:30 |
  | Session II | 13:30–15:49 | 14:00–15:49 |
  | Pre-closing | 15:50–~16:00 | 15:50–~16:00 |
  | Post-trading | ~16:01–16:15 | ~16:01–16:15 |

### Inferences
- **Closing price formation, by period:**
  - Before March 2020: from a pre-closing call auction, for stocks eligible to join it.
  - 2020–2021 (pandemic schedule): session II ended earlier.
  - From 2021-12-06: random close in the last two minutes, with the closing auction for eligible stocks.
  - From December 2024: wider pre-closing coverage.
  - From December 2025: order-locking in the last minutes of pre-closing.

  Each break changes how easy it is to manipulate the close ("marking the close"). Before December 2024, stocks outside LQ45 or the eligible list closed from continuous trading, not an auction. [INF]
- The hiding of broker codes from 2021-12-06 reduces the public data available for detecting broker-level wash trades after that date. [INF]

### Gaps
- The exact date normal (pre-COVID) hours resumed in 2023 was not found. The extracts cite only the end-2022 status and the 2024 pre-closing times.
- The detailed pandemic-era session times were not captured.
- The exact December 2025 decree number was not found. One extract attributes the hours to Kep-00003/BEI/04-2025, which is plausible but unverified.

## 7. Market-wide trading halt thresholds and the dates halts occurred

### Takeaway
- **From March 2020:** a 30-minute halt when the IHSG falls 5% (one source says effective 2020-03-11). Further steps were at 10% and 15% (suspension) [UNCHECKED].
- **From 2025-04-08 (Kep-00002/BEI/04-2025):** 30 minutes at 8%, another 30 minutes at 15%, and a suspension at 20% (to end of session or longer with OJK approval).
- **Halts on record:** 7 in 2020, 2 in 2025 (03-18, 04-08) and 3 in 2026 (01-28, 01-29, 10-16).

### Cited findings
- April 2025 thresholds: halt 1 at more than 8% (30 minutes), halt 2 at more than 15% (30 minutes), and a suspension at more than 20%. [V-multi] — [Bareksa](https://www.bareksa.com/berita/saham/2025-04-08/aturan-baru-bei-soal-trading-halt-berlaku-mulai-8-april-2025-ihsg-bisa-stop-seharian); [Kontan/MomsMoney](https://momsmoney.kontan.co.id/news/bei-tetapkan-auto-rejection-bawah-arb-hanya-15-dan-mengubah-batas-trading-halt-8)
- The 2020 halt rule (halt at a 5% fall) is reported as effective 2020-03-11. [V-single] — cited in [Bisnis 2026-10-16](https://market.bisnis.com/read/20261016/7/2013167/apa-itu-trading-halt-ini-penyebab-dan-catatan-kejadiannya-di-indonesia)
- **Count of halts:** CNBC Indonesia counts 7 in 2020, 2 in 2025 and 3 in 2026. Liputan6 lists 2020 halts on 13, 17, 19, 23 and 30 March and 10 September, which is 6 dates. The likely seventh is 2020-03-12. **Conflict, unresolved.** — [CNBC Indonesia 2026-10-16](https://www.cnbcindonesia.com/research/20261016095125-128-776739/perdagangan-bursa-sempat-alami-trading-halt-ini-aturan-sejarahnya); [Liputan6](https://www.liputan6.com/saham/read/8314523/ihsg-trading-halt-lagi-ini-rekam-jejak-penghentian-perdagangan-saham); [CNBC 2025-04-08](https://www.cnbcindonesia.com/research/20250408100202-128-624156/pengertian-aturan-sejarah-trading-halt-di-bursa-indonesia)
- 2025-03-18: halt under the 5% rule. [V-multi] — same sources
- 2025-04-08: the IHSG opened down 9.19% at 5,912.06 and trading halted at 09:00 WIB. This was the first halt under the 8% rule, after the US tariff shock. [V-multi] — [Kabar Bursa](https://www.kabarbursa.com/market-hari-ini/penjelasan-bei-soal-trading-halt-hari-ini-simak); [Investortrust](https://investortrust.id/market/61993/usai-trading-halt-pertama-ihsg-bei-tunjukkan-perbaikan)
- 2026-01-28 and 2026-01-29: halts triggered by MSCI's freeze of Indonesian index changes over free-float and ownership transparency. [V-multi] — [Periskop](https://periskop.id/pasar-modal/20261016/trading-halt-ihsg-tiga-kali-pada-2026-msci-kembali-guncang-bursa); [Liputan6](https://www.liputan6.com/saham/read/8314523/ihsg-trading-halt-lagi-ini-rekam-jejak-penghentian-perdagangan-saham)
- 2026-10-16: the IHSG fell 8.01% at the open and trading halted, on MSCI's standalone-market consultation. [V-multi] — [CNBC Indonesia](https://www.cnbcindonesia.com/research/20261016095125-128-776739/perdagangan-bursa-sempat-alami-trading-halt-ini-aturan-sejarahnya); [Receh.in](https://www.receh.in/2026/10/ihsg-langsung-trading-halt-usai-anjlok.html)
- Media Indonesia's table puts the 8% threshold "from 2026" and has other inconsistencies. Treat it as unreliable. — [Media Indonesia](https://mediaindonesia.com/ekonomi/854855/sejarah-trading-halt-ihsg-rekam-jejak-rem-darurat-bursa-saham-indonesia)

### Inferences
- On halt days the daily volume covers a shortened session. Flag these dates as abnormal-market days and exclude them from manipulation baselines: 2020-03-12 (unconfirmed), 2020-03-13, 2020-03-17, 2020-03-19, 2020-03-23, 2020-03-30, 2020-09-10, 2025-03-18, 2025-04-08, 2026-01-28, 2026-01-29 and 2026-10-16.

### Gaps
- The 2020 halt decree number was not found. The repo's note that Kompas cites Kep-00024 may refer to it [INF].
- The intermediate 10% and 15% steps of the 2020 rule were not verified.
- The 2020-09-10 halt is unclear. It may have been a stock-level halt or a different event; only Liputan6 lists it.

## 8. Short selling and other rules relevant to wash trades

### Takeaway
Short selling was effectively unavailable through most of 2020–2026. The scheduled 2025-09-29 launch was postponed several times by OJK letters. Short selling started gradually on **2026-09-15**, with the first eligible-stock list effective October 2026. For November 2026, five stocks were removed, and reportedly no stocks remain eligible. No 2015–2026 negotiated-market or cross-trade rule change was found in this pass.

### Cited findings
- OJK letter S-101/D.04/2025 (2025-09-17) postponed the short-selling launch planned for 2025-09-29 to 2026-03-17. [V-multi] — [Investortrust](https://investortrust.id/market/80174/implementasi-short-selling-ditunda-lagi-hingga-2026-alasan-ini-diungkap-bei); [Kumparan](https://kumparan.com/kumparanbisnis/bei-tunda-short-selling-hingga-maret-2026-imbas-ketidakpastian-pasar-global-25vH7EzY0A2)
- A further postponement came through OJK S-9/D.04/2026 (2026-03-13) and IDX Peng-00042/BEI.POP/03-2026 (2026-03-16), to 2026-09-14. [V-multi] — [Detik](https://finance.detik.com/bursa-dan-valas/d-8417795/bei-tunda-lagi-penerapan-short-selling); [MulaMula](https://mulamula.id/short-selling-ditunda-lagi-apa-artinya-untuk-investor-pasar-saham-indonesia/)
- Short-selling financing started gradually on 2026-09-15 under OJK S-113/D.04/2026 (2026-09-09). The eligible-stock list was published on 2026-09-28 and took effect for the October 2026 period. [V-multi] — [Kontan](https://investasi.kontan.co.id/news/mulai-hari-ini-selasa-1592026-bei-berlakukan-short-selling-secara-bertahap); [Detik](https://finance.detik.com/bursa-dan-valas/d-8663166/short-selling-bursa-mulai-berlaku-hari-ini); [Ajaib](https://ajaib.co.id/belajar/berita/short-selling-mulai-berlaku-hari-ini-bei-terbitkan-daftar-saham); [Investortrust](https://investortrust.id/market/116231/bei-kembali-buka-short-selling-berlaku-mulai-besok)
- Peng-00206/BEI.POP/10-2026 (2026-10-28) removed five stocks from the short-selling list for November 2026. Kontan's headline says no stocks are eligible for short selling in November 2026. [V-single each] — [Kontan](https://investasi.kontan.co.id/news/tak-ada-saham-yang-bisa-ditransaksikan-short-selling-pada-periode-november-2026)

### Inferences
- The two November 2026 reports fit together if the October list contained only five stocks. [INF]
- For a detector, short-sale volume is negligible for the whole 2015–November 2026 sample. Price drops are not explained by covered shorting. Hidden broker codes after 2021-12-06 and the lack of public cross-trade flags limit wash-trade detection from daily data alone. [INF]

### Gaps
- The March 2020 OJK and IDX short-selling ban, and whether it was ever formally lifted before 2025, were not verified in this pass.
- No changes to negotiated-market or cross-trade rules (Peraturan II-A) between 2015 and 2026 were found. A dedicated search is needed.

## 9. Board structure changes

### Takeaway
The boards in use: Main and Development (pre-2015); Acceleration Board (2019, minimum price Rp1); Papan Pemantauan Khusus (stage I on 2023-06-12, stage II FCA on 2024-03-25); and the New Economy Board, which was in existence by April 2025 because the April 2025 ARB decree covers it. The New Economy Board launch date was not found.

### Cited findings
- The April 2025 and October 2026 ARB decrees apply to the "papan utama, papan pengembangan, dan papan ekonomi baru". [V-multi] — [Hukumonline](https://www.hukumonline.com/berita/a/bei-lakukan-penyesuaian-aturan-perdagangan-efek-lt67f4abb2a449a?page=all); [Republika](https://ekonomi.republika.co.id/berita/tn6s16370/bursa-efek-indonesia-perbarui-ketentuan-auto-reject-bawah-untuk-saham-harga-rendah)
- Acceleration Board design in 2019: [Pasardana](https://pasardana.id/news/2019/5/28/papan-akselerasi-mungkinkan-investor-beli-saham-rp-1/). Board overview: [Ajaib](https://ajaib.co.id/mengenal-papan-utama-pengembangan-dan-akselerasi-di-bursa/)
- Papan Pemantauan Khusus milestones: see section 2.

### Gaps
- The launch dates and decree numbers for the New Economy Board and the Acceleration Board were not found in this pass. The Acceleration Board rule is likely Peraturan I-V (2019) [INF].
