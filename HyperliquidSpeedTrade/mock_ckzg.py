"""
ckzgのモックモジュール
Windows環境でビルドできないckzgの代替として、必要最小限の機能を提供します。
注意: EIP-4844の高度な機能は使用できません（Hyperliquidでは不要）
"""

# ckzgが必要とする関数のモック
def blob_to_kzg_commitment(*args, **kwargs):
    raise NotImplementedError("ckzg functionality is not available in this environment")

def compute_blob_kzg_proof(*args, **kwargs):
    raise NotImplementedError("ckzg functionality is not available in this environment")

def verify_blob_kzg_proof(*args, **kwargs):
    raise NotImplementedError("ckzg functionality is not available in this environment")

def verify_blob_kzg_proof_batch(*args, **kwargs):
    raise NotImplementedError("ckzg functionality is not available in this environment")

