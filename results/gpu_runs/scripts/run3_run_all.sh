#!/bin/bash
# Runs on the Vast instance. Token is read from a 600 file, never printed.
cd /root/repo
export HF_TOKEN=$(cat /root/.hf_token) HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
mkdir -p /root/logs
L=/root/logs/queue.log
echo "$(date -u +%FT%TZ) SMALL START" | tee -a $L
if [ ! -f /root/logs/small.done ]; then
  UZB_DEVICE=cuda python scripts/run_models.py --only mGPT mGPT-Uzbek Glot500 "XLM-R large" --batch-size 64 > /root/logs/small.log 2>&1
  echo "$(date -u +%FT%TZ) SMALL END rc=$?" | tee -a $L; touch /root/logs/small.done
  rm -rf /root/.cache/huggingface/hub/models--* /root/.cache/huggingface/xet
fi
run_queue() {
while read -r model dtype bs out keep; do
  [ -z "$model" ] && continue
  tag=$(echo "$model" | tr '/' '_')_$dtype
  [ -f /root/logs/$tag.done ] && continue
  echo "$(date -u +%FT%TZ) START $model $dtype" | tee -a $L
  t0=$(date +%s)
  python scripts/run_big.py --model "$model" --dtype "$dtype" --batch-size "$bs" --out "$out" > /root/logs/$tag.log 2>&1
  rc=$?
  if [ $rc -ne 0 ] && grep -q "OutOfMemory" /root/logs/$tag.log; then
    echo "OOM, retry with batch 4" >> $L
    python scripts/run_big.py --model "$model" --dtype "$dtype" --batch-size 4 --out "$out" >> /root/logs/$tag.log 2>&1; rc=$?
  fi
  echo "$(date -u +%FT%TZ) END $model $dtype rc=$rc secs=$(( $(date +%s)-t0 ))" | tee -a $L
  touch /root/logs/$tag.done
  rm -rf /root/.cache/huggingface/hub/models--* /root/.cache/huggingface/xet
done < $1
}
run_queue /root/queue_causal.txt
echo "$(date -u +%FT%TZ) CAUSALDONE" | tee -a $L
# Gemma only if the box placed the go file (licence accepted)
for i in $(seq 1 3); do [ -f /root/gemma.go ] || [ -f /root/gemma.skip ] && break; sleep 60; done
[ -f /root/gemma.go ] && run_queue /root/queue_gemma.txt
echo "$(date -u +%FT%TZ) ALLDONE" | tee -a $L
