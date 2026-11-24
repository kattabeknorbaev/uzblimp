#!/bin/bash
# Runs on the Vast instance. One model at a time; a failure skips to the next model.
cd /root/repo
export HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
mkdir -p /root/logs
while read -r model dtype bs out keep; do
  [ -z "$model" ] && continue
  tag=$(echo "$model" | tr '/' '_')_$dtype
  [ -f /root/logs/$tag.done ] && continue
  echo "$(date -u +%FT%TZ) START $model $dtype" | tee -a /root/logs/queue.log
  t0=$(date +%s)
  python scripts/run_big.py --model "$model" --dtype "$dtype" --batch-size "$bs" --out "$out" > /root/logs/$tag.log 2>&1
  rc=$?
  if [ $rc -ne 0 ] && grep -q "OutOfMemory" /root/logs/$tag.log; then
    echo "OOM, retry with batch 4" >> /root/logs/queue.log
    python scripts/run_big.py --model "$model" --dtype "$dtype" --batch-size 4 --out "$out" >> /root/logs/$tag.log 2>&1; rc=$?
  fi
  echo "$(date -u +%FT%TZ) END $model $dtype rc=$rc secs=$(( $(date +%s)-t0 ))" | tee -a /root/logs/queue.log
  touch /root/logs/$tag.done
  [ "$keep" = "keep=yes" ] || rm -rf /root/.cache/huggingface/hub/models--* /root/.cache/huggingface/hub/blobs /root/.cache/huggingface/xet
done < /root/queue.txt
echo "$(date -u +%FT%TZ) ALLDONE" | tee -a /root/logs/queue.log
