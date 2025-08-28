from transformers import AutoConfig
cfg = AutoConfig.from_pretrained("facebook/nllb-200-distilled-600M")
tasks = [k for k in cfg.task_specific_params if k.startswith("translation")]
print(tasks)