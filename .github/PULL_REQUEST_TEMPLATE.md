<!-- 貢献ありがとうございます。CONTRIBUTING.md も併せてご確認ください。 -->

## 変更内容

<!-- 何を・なぜ変更したかを簡潔に。関連 Issue があれば #番号 で参照。 -->

## 対象モデル / 領域

- [ ] 01-foc-ideal-voltage
- [ ] 02-foc-pwm-drive
- [ ] 03-foc-pwm-eps
- [ ] 04-foc-pwm-sensorless
- [ ] 05-foc-pwm-eps-sensorless
- [ ] 共通 (docs / CI / scripts / common)

## チェックリスト

- [ ] 触れたモデルが `cmake --build` でビルドできる
- [ ] `ctest` が通る(スモーク＋数値テスト)
- [ ] `sim_params.hpp` / `eps_sim_params.hpp` のパラメータを変更した場合、回帰リファレンス CSV を再生成して含めた
- [ ] コードスタイル(スペース4・C++20・`[[nodiscard]]`)に従っている
- [ ] 必要に応じてドキュメント(`docs/` や各 `README.md`)を更新した
