import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans 
from sklearn.metrics import silhouette_score
from joblib import dump

raw = pd.read_csv('user_data.csv')
features = raw[['Food','Transport','Entertainment','Grocery','Others','Total']]
fr = pd.DataFrame()
categories = ['Food','Transport','Entertainment','Grocery','Others']

for i in categories:
    fr[i+'Ratio'] = features[i]/features['Total']*100


scaler = StandardScaler()
scaled_data = scaler.fit_transform(fr)
# 使用 elbow method 找出最佳 k 值
""""" Best k is 3
inertias = []
K = range(1, 11)  # 試 k = 1~10 群

for k in K:
    model = KMeans(n_clusters=k, random_state=42)
    model.fit(scaled_data)  # 用標準化後的資料
    inertias.append(model.inertia_)  # 存下每次的誤差

# 畫出肘點圖
plt.plot(K, inertias, marker='o')
plt.title('Elbow Method:k')
plt.xlabel('k')
plt.ylabel('Inertia')
plt.xticks(K)
plt.grid(True)
plt.tight_layout()
plt.show()

from sklearn.metrics import silhouette_score

scores = []
K = range(2, 11)  # 只能從 k=2 開始，因為 silhouette k=1 無效

for k in K:
    model = KMeans(n_clusters=k, random_state=42)
    labels = model.fit_predict(scaled_data)
    score = silhouette_score(scaled_data, labels)
    scores.append(score)

# 畫圖
plt.plot(K, scores, marker='o')
plt.title('Silhouette Score')
plt.xlabel('k')
plt.ylabel('The higher the better')
plt.xticks(K)
plt.grid(True)
plt.tight_layout()
plt.show()

"""

model = KMeans(n_clusters=3, random_state=42)
labels = model.fit_predict(scaled_data)
fr['Cluster'] = labels

# 計算每群平均比例（用來畫圖）
group_avg = fr.groupby('Cluster').mean().round(2)

# 視覺化群組消費特徵
group_avg.T.plot(kind='bar', figsize=(10, 6))
plt.title('Average Expense per Cluster (%)')
plt.ylabel('Average Ratio (%)')
plt.xlabel('Category')
plt.xticks(rotation=0)
plt.legend(title='Cluster')
plt.tight_layout()
plt.show()

# 儲存模型
dump(model, 'kmeans_model.joblib')
dump(scaler, 'scaler.joblib')

