# 参考文献

`bldc-foc-sim` および付属のプレゼンテーション資料が参照する文献・資料を
まとめる。

> **注記**
> 本ファイルは付属プレゼンテーション資料 (v8) の出典記載をもとに作成した
> 暫定版である。書誌情報の一部 (著者・巻号・ページ等) は今後補完される。

---

## 1. モータ・ベクトル制御

- ルネサス エレクトロニクス「ブラシレス DC モータ — 基礎編」
  技術解説 (エンジニアスクール)
  <https://www.renesas.com/jp/ja/support/technical-resources/engineer-school/brushless-dc-motor-01-overview.html>

- ルネサス エレクトロニクス「ブラシレス DC モータ — インバータと PWM」
  技術解説 (エンジニアスクール)
  <https://www.renesas.com/jp/ja/support/technical-resources/engineer-school/brushless-dc-motor-02-inverter-pmw.html>

- 日本電産 (ニデック)「モータの基礎知識」
  <https://www.nidec.com/jp/technology/motor/basic/00005/>

- ICCAS 2005 (International Conference on Control, Automation and Systems
  2005) — ベクトル制御・センサーレス制御に関する発表論文。
  ※ 具体的な論文タイトル・著者は補完予定。

---

## 2. モータ諸元 (シミュレーションパラメータの根拠)

- ATO 110WDM06020 ブラシレス DC モータ データシート
  本コードの定格電圧 (48 V)、極対数、トルク定数などのパラメータ設定の
  参考とした製品データシート。

---

## 3. 機能安全 (付属プレゼン資料の機能安全パート)

- ISO 26262-3:2018 *Road vehicles — Functional safety —
  Part 3: Concept phase*
  HARA (ハザード分析・リスクアセスメント)、ASIL 決定、安全目標の
  導出に関する規格。

- AIS (Abbreviated Injury Scale) — シビアリティ (S) 評価の参考尺度。

---

## 4. リポジトリ内の関連資料

| 資料 | 内容 |
|------|------|
| [`derivations.md`](derivations.md) | 本コードで用いる数式の導出 |
| [`glossary.md`](glossary.md) | 用語集 |
| [theory/](theory/motor-model.md) | モータモデル・FOC・PWM・PI・センサーレス・EPS の解説 |
| 付属プレゼンテーション資料 | 三相ブラシレスモーター制御 / 電動パワーステアリング (v8) |

---

## 5. 補完予定の項目

以下の書誌情報は今後追記される。

- ICCAS 2005 の該当論文の正式タイトル・著者・ページ番号
- ベクトル制御・センサーレス制御の標準的な教科書 (例: モータドライブ
  制御に関する書籍) の書誌情報
- EPS 機構モデルの根拠とした文献
