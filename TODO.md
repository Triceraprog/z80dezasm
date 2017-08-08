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
- Automatic labeling
  loopADDR when JR, -bla
  skipADDR when JR, +bla
  callADDR when CALL
  jumpADDR when JP
    Adding the calling addresses in comments
- Detect jump on partial instructions tricks (0x101a/0x101b)
