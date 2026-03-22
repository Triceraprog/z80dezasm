    ; This is the source file used to produce the example
    ; It is assembled with:
    ; sjasmplus --raw=example.rom example-source.asm

    org $0000

start:
    di
    jp main

    ds $0008 - $
rst08:
    ret

    ds $0010 - $
rst10:
    ret

    ds $0018 - $
rst18:
    ret

    ds $0020 - $
rst20:
    ret

    ds $0028 - $
rst28:
    ret

    ds $0030 - $
rst30:
    ret

    ds $0038 - $
rst38:
    jp irq

    ds $0066 - $
nmi:
    retn

irq:
    call handler_irq
    ret

message:
    byte "Hello, World!", 0
    byte 0xff, 0x30, 0xff, 0x40, 0xff, 0x50, 0xff, 0x60, 0xff

main:
    ei
infinite_loop:
    jp infinite_loop

handler_irq:
    push af
    push bc
    push de
    push hl

    ld hl, message
    call print_string

    pop hl
    pop de
    pop bc
    pop af
    ret

print_string:
    ld a, (hl)
    or a
    ret z
    rst 8
    inc hl
    jp print_string
