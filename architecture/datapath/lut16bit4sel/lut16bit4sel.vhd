-- Library
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use work.lutConst.all;

-- Define entity
entity lut16bit4sel is
	generic	(
		Table	:	LutArray										-- isi tabel: SHIFT_LUT atau ATANH_LUT (lutConst)
    );
	port	(
		Sel		:	in		std_logic_vector (3 downto 0);		-- alamat tabel (langkah k, 0-15)
		Data	:	out		std_logic_vector (15 downto 0)		-- luaran isi tabel pada alamat Sel
    );
end lut16bit4sel;

-- Define architecture
architecture behavioral of lut16bit4sel is
begin
	-- baca entri tabel pada alamat Sel.
	Data <= Table(to_integer(unsigned(Sel)));
end behavioral;
