# bldc-foc-sim 理論ドキュメント

三相ブラシレスモータ (BLDC / PMSM) のベクトル制御 (FOC) と電動パワーステアリング (EPS) に関する理論資料です。

---

## 理論ドキュメント一覧

| ドキュメント | 内容 |
|-------------|------|
| [モータモデル](theory/motor-model.md) | dq 軸電圧方程式・機械方程式・離散化 |
| [座標変換](theory/coordinate-transform.md) | Clarke 変換・Park 変換の数学 |
| [ベクトル制御 (FOC)](theory/foc.md) | PI 制御・デカップリング・A/B 型モデル比較 |
| [PI ゲイン設計](theory/pi-tuning.md) | 極配置法によるゲイン算出 |
| [PWM インバータ](theory/pwm-inverter.md) | 三相ブリッジ・中点変調・電圧飽和解析 |
| [センサーレス制御](theory/sensorless.md) | 誘起電圧オブザーバ・PLL・起動シーケンス |
| [電動パワーステアリング](theory/eps.md) | EPS 機構・アシストマップ・制御ブロック図 |
| [機能安全](theory/functional-safety.md) | HARA・ASIL・ISO 26262 安全要求導出フロー |

---

## ドキュメントの読み方

```
motor-model.md          ← モータの基礎方程式を理解する
      │
coordinate-transform.md ← 座標変換 (Clarke/Park) を理解する
      │
foc.md                  ← ベクトル制御の全体像を把握する
      │
pi-tuning.md            ← PI ゲインの設計法を学ぶ
      │
pwm-inverter.md         ← PWM 駆動の現実的な制約を理解する
      │
sensorless.md           ← 位置センサレス制御を学ぶ
      │
eps.md                  ← EPS への応用を理解する
      │
functional-safety.md    ← 機能安全 (HARA / ISO 26262) を理解する
```

---

## ローカルでの閲覧

```sh
pip install -r requirements-docs.txt
mkdocs serve
```

ブラウザで `http://localhost:8000` を開くと数式が正しくレンダリングされます。
