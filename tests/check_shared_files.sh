#!/usr/bin/env bash
# =============================================================================
#  check_shared_files.sh  —  モデル間で同一であるべき共有ファイルの一致検査
# -----------------------------------------------------------------------------
#  bldc-foc-sim は各モデルを自己完結 (src/ に全ソースを保持) とする教材設計上、
#  座標変換・CSV 照合など「本来どのモデルでも同一」のファイルが物理的に複製される。
#  複製が静かにドリフトするのを防ぐため、下記ファイルが全モデルでバイト一致で
#  あることを検査する。CI (consistency ジョブ) とローカルの両方から実行できる。
#
#  使い方 : bash tests/check_shared_files.sh   (リポジトリのルートで実行)
#  終了コード : 一致=0 / 逸脱=1
# =============================================================================
set -u

SHARED_FILES=(
    motor_vector_conv.hpp
    motor_vector_conv.cpp
    csv_verifier.hpp
    csv_verifier.cpp
)

fail=0
for f in "${SHARED_FILES[@]}"; do
    # 各モデル (先頭が数字のディレクトリ) の src/ にある同名ファイルを集める。
    mapfile -t paths < <(ls -1 [0-9]*/src/"$f" 2>/dev/null)
    if [ "${#paths[@]}" -lt 2 ]; then
        echo "SKIP: $f (present in ${#paths[@]} model(s))"
        continue
    fi
    distinct=$(md5sum "${paths[@]}" | awk '{print $1}' | sort -u | wc -l)
    if [ "$distinct" -ne 1 ]; then
        echo "FAIL: $f diverges across models ($distinct distinct versions)"
        md5sum "${paths[@]}"
        fail=1
    else
        echo "OK:   $f identical across ${#paths[@]} models"
    fi
done

if [ "$fail" -ne 0 ]; then
    echo ""
    echo "共有ファイルがモデル間でドリフトしています。正典 (canonical) を全モデルへ複製してください。"
    exit 1
fi
echo ""
echo "全共有ファイルがモデル間で一致しています。"
exit 0
