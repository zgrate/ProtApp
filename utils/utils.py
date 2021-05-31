def crc8(data):
    crc = 0
    for i in range(len(data)):
        byte = data[i]
        for b in range(8):
            fb_bit = (crc ^ byte) & 0x01
            if fb_bit == 0x01:
                crc = crc ^ 0x18
            crc = (crc >> 1) & 0x7f
            if fb_bit == 0x01:
                crc = crc | 0x80
            byte = byte >> 1
    return crc

#
#
# uint8_t crc8( uint8_t *addr, uint8_t len) {
#       uint8_t crc=0;
#       for (uint8_t i=0; i<len;i++) {
#          uint8_t inbyte = addr[i];
#          for (uint8_t j=0;j<8;j++) {
#              uint8_t mix = (crc ^ inbyte) & 0x01;
#              crc >>= 1;
#              if (mix)
#                 crc ^= 0x8C;
#          inbyte >>= 1;
#       }
#     }
#    return crc;
# }