"""
Dummy ckzg module for Windows compatibility
EIP-4844 blob functionality is not available
"""

def load_trusted_setup(*args, **kwargs):
    """Dummy load_trusted_setup - does nothing"""
    pass

def blob_to_kzg_commitment(*args, **kwargs):
    raise NotImplementedError("ckzg not available on this platform")

def compute_blob_kzg_proof(*args, **kwargs):
    raise NotImplementedError("ckzg not available on this platform")

def verify_blob_kzg_proof(*args, **kwargs):
    raise NotImplementedError("ckzg not available on this platform")

def verify_blob_kzg_proof_batch(*args, **kwargs):
    raise NotImplementedError("ckzg not available on this platform")

# EIP-4844用の定数
BYTES_PER_FIELD_ELEMENT = 32
FIELD_ELEMENTS_PER_BLOB = 4096

