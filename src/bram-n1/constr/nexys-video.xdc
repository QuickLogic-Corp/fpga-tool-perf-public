# Clock Signal
set_property LOC R4 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]

# UART tx and
set_property LOC V18 [get_ports ser_tx]
set_property LOC AA19 [get_ports ser_rx]
set_property IOSTANDARD LVCMOS33 [get_ports ser_tx]
set_property IOSTANDARD LVCMOS33 [get_ports ser_rx]

# Switches
set_property LOC E22 [get_ports {sw[0]}]
set_property LOC F21 [get_ports {sw[1]}]
set_property LOC G21 [get_ports {sw[2]}]
set_property LOC G22 [get_ports {sw[3]}]
set_property LOC H17 [get_ports {sw[4]}]
set_property LOC J16 [get_ports {sw[5]}]
set_property LOC K13 [get_ports {sw[6]}]
set_property LOC M17 [get_ports {sw[7]}]
# Pmod header JA
set_property LOC AB22  [get_ports {sw[8]}]
set_property LOC AB21  [get_ports {sw[9]}]
set_property LOC AB20  [get_ports {sw[10]}]
set_property LOC AB18  [get_ports {sw[11]}]
set_property LOC Y21   [get_ports {sw[12]}]
set_property LOC AA21  [get_ports {sw[13]}]
set_property LOC AA20  [get_ports {sw[14]}]
set_property LOC AA18  [get_ports {sw[15]}]

set_property IOSTANDARD LVCMOS33 [get_ports {sw[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[8]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[9]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[10]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[12]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[13]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[14]}]
set_property IOSTANDARD LVCMOS33 [get_ports {sw[15]}]
# Leds
set_property LOC T14 [get_ports {led[0]}]
set_property LOC T15 [get_ports {led[1]}]
set_property LOC T16 [get_ports {led[2]}]
set_property LOC U16 [get_ports {led[3]}]
set_property LOC V15 [get_ports {led[4]}]
set_property LOC W16 [get_ports {led[5]}]
set_property LOC W15 [get_ports {led[6]}]
set_property LOC Y13 [get_ports {led[7]}]
# Pmod header JB
set_property LOC V9 [get_ports {led[8]}]
set_property LOC V8  [get_ports {led[9]}]
set_property LOC V7  [get_ports {led[10]}]
set_property LOC W7  [get_ports {led[11]}]
set_property LOC W9  [get_ports {led[12]}]
set_property LOC Y9  [get_ports {led[13]}]
set_property LOC Y8  [get_ports {led[14]}]
set_property LOC Y7  [get_ports {led[15]}]

set_property IOSTANDARD LVCMOS33 [get_ports {led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[4]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[5]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[6]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[7]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[8]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[9]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[10]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[11]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[12]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[13]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[14]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[15]}]

create_clock -period 10.0 [get_ports clk]
