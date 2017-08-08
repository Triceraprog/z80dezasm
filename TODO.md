- The masks for opcode decoding can be optimized by complete masking and hashing
- Is separation between REGISTERs and REGISTER_PAIRs necessary?
- Comments and labels at specific adresses
- Labels with code or data
- Decoding
  - Every memorized address is added as a label
- Labels
  - Labels are loaded with "address", "name"
- Comments
  - Comments are loaded with either
    - "Comment: address/label place (block above or default/right" CR "comment"
    - "Comment: address/label comment on one line"
- Rename Ranges to Regions
- Try to detect strings to turn DEFB to DEFM
- Merge labels and references parsing
- Replace calling addresses with label names
- Label data reference too
- Detect jump on partial instructions tricks (0x101a/0x101b)
  - Two cases
    - First is when a label has no decoded instruction
    - Second is when a decoded instruction is following another one without the right number of bytes
  - The first instruction is turned to DEFB with the number of needed bytes
  - A comment is added after DEFB

Example:
             defb     $28             ; $2860 28              ; partial instruction trick
;            jr       z,$288d         ; $2860 28 2b           ; <- reads as
             
call2861:    dec      hl              ; $2861 2b              ; called from: $0a7c,$261a,$284d
