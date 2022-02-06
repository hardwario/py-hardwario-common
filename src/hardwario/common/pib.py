import struct
import array


class PIB:

    SIGNATURE = (0, '<L')
    VERSION = (4, 'B')
    SIZE = {
        1: (0x08, '<H'),
        2: (0x05, '<B')
    }
    SERIAL_NUMBER = {
        1: (0x0c, '<L'),
        2: (0x06, '<L')
    }
    HW_REVISION = {
        1: (0x10, '<H'),
        2: (0x0a, '<H')
    }
    HW_VARIANT = {
        1: (0x14, '<L'),
        2: (0x0c, '<L')
    }
    VENDOR_NAME = {
        1: (0x18, '<32s'),
        2: (0x10, '<32s')
    }
    PRODUCT_NAME = {
        1: (0x38, '<32s'),
        2: (0x30, '<32s')
    }

    RF_OFFSET = (88, 2, '<h')
    RF_CORRECTION = (88, 4, '<L')

    def __init__(self, version=1, buf=None):
        self._buf = array.array('B', [0xff] * 128)
        self._default_version = version
        if version == 1:
            self._default_size = 92  # 0x58 + 4
        elif version == 2:
            self._default_size = 84  # 0x50 + 4
        else:
            raise Exception('PIB failed version')

        self._is_core_module = False
        self._has_rf_correction = False

        if buf is not None:
            self.load(buf)
        else:
            self.reset()

    def load(self, buf):
        for i, v in enumerate(buf):
            self._buf[i] = v

        self._update_family()

        if self.get_signature() != 0xbabecafe:
            raise Exception('Integrity check for PIB failed signature')
        if self.get_version() in (1, 2):
            raise Exception('Integrity check for PIB failed version')
        if self.get_size() != self._size:
            raise Exception('Integrity check for PIB failed size')
        if self.get_crc() != self.calc_crc():
            raise Exception('Integrity check for PIB failed crc')

    def reset(self):
        self._size = self._default_size
        for i in range(128):
            self._buf[i] = 0xff
        self._pack(self.SIGNATURE, 0xbabecafe)
        self._pack(self.VERSION, self._default_version)
        self.set_vendor_name('')
        self.set_product_name('')
        self._is_core_module = False
        self._has_rf_correction = False
        self._pack(self.SIZE, self._size)

    def _update_family(self):
        self._size = self._default_size
        self._is_core_module = False

        family = self.get_family()
        if family in (0x101, 0x102, 0x103, 0x104):
            self._size += 4
            self._is_core_module = True
            self.set_rf_offset(-32768)  # default invalid value
        elif family == 0x0009:  # STICKER
            self._size += 4
            self._has_rf_correction = True
            self.set_rf_correction(0xffffffff)

    def get_signature(self):
        return self._unpack(self.SIGNATURE)

    def get_version(self):
        return self._unpack(self.VERSION)

    def get_size(self):
        return self._unpack(self.SIZE)

    def get_serial_number(self):
        return self._unpack(self.SERIAL_NUMBER)

    def set_serial_number(self, value):
        if (value & 0xc0000000) != 0x80000000:
            raise Exception('Bad serial number format')
        self._pack(self.SERIAL_NUMBER, value)
        self._update_family()
        self._pack(self.SIZE, self._size)

    def get_hw_revision(self):
        return self._unpack(self.HW_REVISION)

    def set_hw_revision(self, value):
        self._pack(self.HW_REVISION, value)

    def get_hw_variant(self):
        return self._unpack(self.HW_VARIANT)

    def set_hw_variant(self, value):
        self._pack(self.HW_VARIANT, value)

    def get_vendor_name(self):
        return '%s' % self._unpack(self.VENDOR_NAME).decode('ascii').rstrip('\0')

    def set_vendor_name(self, value):
        self._pack(self.VENDOR_NAME, value.encode())

    def get_product_name(self):
        return self._unpack(self.PRODUCT_NAME).decode('ascii').rstrip('\0')

    def set_product_name(self, value):
        self._pack(self.PRODUCT_NAME, value.encode())

    def get_rf_offset(self):
        if not self._is_core_module:
            raise Exception('Only CORE module')
        return self._unpack(self.RF_OFFSET)

    def set_rf_offset(self, value):
        if not self._is_core_module:
            raise Exception('Only CORE module')
        self._pack(self.RF_OFFSET, value)

    def get_rf_correction(self):
        if not self._has_rf_correction:
            raise Exception('This device has no RF correction')
        return self._unpack(self.RF_CORRECTION)

    def set_rf_correction(self, value):
        if not self._has_rf_correction:
            raise Exception('This device has no RF correction')
        self._pack(self.RF_CORRECTION, value)

    def get_crc(self):
        return struct.unpack_from('<L', self._buf, self._size - 4)[0]

    def get_buffer(self):
        crc = self.calc_crc()
        struct.pack_into('<L', self._buf, self._size - 4, crc)
        return self._buf.tobytes()

    def get_family(self):
        sn = self.get_serial_number()
        if (sn & 0xc0000000) != 0x80000000:
            raise Exception('Bad serial number format')
        return (sn >> 20) & 1023

    def get_dict(self):
        payload = {
            'signature': '0x%08x' % self.get_signature(),
            'version': '0x%02x' % self.get_version(),
            'size': '0x%04x' % self.get_size(),
            'serial_number': '0x%08x' % self.get_serial_number(),
            'hw_revision': '0x%04x' % self.get_hw_revision(),
            'hw_variant': '0x%08x' % self.get_hw_variant(),
            'vendor_name': self.get_vendor_name(),
            'product_name': self.get_product_name(),
            'crc': '0x%08x' % self.get_crc()
        }

        if self._is_core_module:
            payload['rf_offset'] = self.get_rf_offset()
        if self._has_rf_correction:
            payload['rf_correction'] = self.get_rf_correction()

        return payload

    def calc_crc(self):
        if self.get_version() == 1:
            crc = 0xffffffff
            crc = self._calc_crc_item(crc, self.SIGNATURE)
            crc = self._calc_crc_item(crc, self.VERSION)
            crc = self._calc_crc_item(crc, self.SIZE)
            crc = self._calc_crc_item(crc, self.SERIAL_NUMBER)
            crc = self._calc_crc_item(crc, self.HW_REVISION)
            crc = self._calc_crc_item(crc, self.HW_VARIANT)
            crc = self._calc_crc_item(crc, self.VENDOR_NAME)
            crc = self._calc_crc_item(crc, self.PRODUCT_NAME)
            if self._is_core_module:
                crc = self._calc_crc_item(crc, self.RF_OFFSET)
            if self._has_rf_correction:
                crc = self._calc_crc_item(crc, self.RF_CORRECTION)
            return crc
        else:
            return self._calc_crc(0, 0, self._size - 4)

    def _pack(self, mem, data):
        if isinstance(mem, dict):
            mem = mem[self.get_version()]
        offset, fmt = mem
        struct.pack_into(fmt, self._buf, offset, data)

    def _unpack(self, mem):
        if isinstance(mem, dict):
            mem = mem[self.get_version()]
        offset, fmt = mem
        return struct.unpack_from(fmt, self._buf, offset)[0]

    def _calc_crc_item(self, crc, mem):
        if isinstance(mem, dict):
            mem = mem[self.get_version()]
        offset, fmt = mem
        size = struct.calcsize(fmt)
        return self._calc_crc(crc, offset, size)

    def _calc_crc(self, crc, offset, size):
        for i in range(offset, offset + size):
            n = self._buf[i]
            crc ^= n
            for _ in range(8):
                crc = (crc >> 1) ^ (0xedb88320 & ~((crc & 1) - 1))
        return crc ^ 0xffffffff
