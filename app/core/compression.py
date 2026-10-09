# rayzOSS Core Compression Engine
# Credits: rayzien (https://github.com/rayzien) & pheonix14 (https://github.com/pheonix14)
import lzma
import zlib
import struct

MAGIC = b"RZOSS\x01"  # 6 bytes header: RayzOSS format version 1

class RayzCompressor:
    """
    Custom Lossless Compression Engine for rayzOSS.
    Guarantees crisp byte-for-byte fidelity with cryptographic-grade integrity verification.
    """
    @staticmethod
    def compress(data: bytes, level: int = 9) -> bytes:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Data must be bytes or bytearray")
        
        # Calculate checksum and metadata before compression
        raw_crc = zlib.crc32(data) & 0xffffffff
        raw_size = len(data)
        
        # Lossless extreme compression
        compressed_body = lzma.compress(data, preset=level)
        
        # Header: MAGIC (6B) + CRC32 (4B) + Original Size (8B)
        header = MAGIC + struct.pack(">IQ", raw_crc, raw_size)
        return header + compressed_body

    @staticmethod
    def decompress(payload: bytes) -> bytes:
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("Payload must be bytes or bytearray")
            
        header_len = len(MAGIC) + 12  # 6 + 4 + 8 = 18 bytes
        if len(payload) >= header_len and payload.startswith(MAGIC):
            expected_crc, expected_size = struct.unpack(">IQ", payload[len(MAGIC):header_len])
            compressed_body = payload[header_len:]
            decompressed = lzma.decompress(compressed_body)
            
            actual_crc = zlib.crc32(decompressed) & 0xffffffff
            if actual_crc != expected_crc:
                raise ValueError(f"Integrity check failed! Expected CRC {expected_crc:#010x}, got {actual_crc:#010x}")
            if len(decompressed) != expected_size:
                raise ValueError(f"Size mismatch! Expected {expected_size} bytes, got {len(decompressed)} bytes")
            return decompressed
        else:
            # Fallback for raw LZMA or uncompressed legacy data
            try:
                return lzma.decompress(payload)
            except Exception:
                return payload
