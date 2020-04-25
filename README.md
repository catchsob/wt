# wtit
這是什麼樹？

目標: 樹型與樹葉辨識與偵測

範圍:
1. 針對黑板樹、茄冬、樟樹、鳳凰木、榕樹、台灣欒樹、楓香、苦楝、白千層、水黃皮、阿勃勒、大王椰子、大葉欖仁、小葉欖仁等 14 種樹形的影像辨識與物件偵測模型建立
2. 針對青楓、鳳凰木、水同木、稜果榕、楓香、大葉山欖、盾柱木、大葉欖仁等 8 種樹葉的影像辨識與物件偵測模型建立
3. 樹形與樹葉影像辨識與物件偵測模型整合至 Android APP
4. 樹形與樹葉影像辨識與物件偵測模型整合至 Line Chatbot

AI 模型解決方案:
1. 自力拍攝並精選
2. 發展 Central-Attention CNN 概念，擷取照片中央區塊進行訓練以加速模型收斂
3. 嘗試 dual-path 模型訓練並混用 Inception 模塊，提升模型精確度
4. 嘗試 MobileNetV2、Inception 等不同網路以取得各種條件限制下的最佳模型

系統整合方案:
1. Android APP - 基於 https://github.com/tensorflow/examples/tree/master/lite/examples/image_classification/android ，整合開發即時辨識機制
2. Line Chatbot: 以 GCP 建立雲端 AI inference backend，並開發前端 Line Chatbot 應用

目錄:
1. root: AI modeling for tree classification, by CACNN mixed with Inception and CACNN only
2. wt: 什麼樹？Line Chatbot version
3. wtlive: 什麼樹？Android APP version
