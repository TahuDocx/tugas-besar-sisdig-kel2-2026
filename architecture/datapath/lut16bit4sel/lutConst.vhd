-- Library
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Define package
-- konstanta tabel CORDIC hiperbolik, diindeks langkah k = 0-15 (keluaran counter4bit).
-- nilai dibangkitkan dari cordic-sim-py/cordic.py: run(..., n=16, FixedFormat(width=16, frac=14)).
package lutConst is
	-- tipe tabel 16 entri x 16 bit, dipakai sebagai generic Table pada lut16bit4sel.
	type LutArray is array (0 to 15) of std_logic_vector (15 downto 0);

	-- jadwal geser i per langkah k: 1,2,3,4,4,5,...,13,13,14 (i = 4 dan 13 diulang
	-- agar CORDIC hiperbolik konvergen). datapath memakai 4 bit bawah untuk shifter16bit.
	constant SHIFT_LUT	:	LutArray := (
		std_logic_vector(to_unsigned(1, 16)),
		std_logic_vector(to_unsigned(2, 16)),
		std_logic_vector(to_unsigned(3, 16)),
		std_logic_vector(to_unsigned(4, 16)),
		std_logic_vector(to_unsigned(4, 16)),
		std_logic_vector(to_unsigned(5, 16)),
		std_logic_vector(to_unsigned(6, 16)),
		std_logic_vector(to_unsigned(7, 16)),
		std_logic_vector(to_unsigned(8, 16)),
		std_logic_vector(to_unsigned(9, 16)),
		std_logic_vector(to_unsigned(10, 16)),
		std_logic_vector(to_unsigned(11, 16)),
		std_logic_vector(to_unsigned(12, 16)),
		std_logic_vector(to_unsigned(13, 16)),
		std_logic_vector(to_unsigned(13, 16)),
		std_logic_vector(to_unsigned(14, 16))
	);

	-- atanh(2^-i) per langkah k dalam Q2.14 (round(atanh(2^-i) * 2^14)),
	-- i mengikuti SHIFT_LUT pada indeks yang sama.
	constant ATANH_LUT	:	LutArray := (
		std_logic_vector(to_signed(9000, 16)),
		std_logic_vector(to_signed(4185, 16)),
		std_logic_vector(to_signed(2059, 16)),
		std_logic_vector(to_signed(1025, 16)),
		std_logic_vector(to_signed(1025, 16)),
		std_logic_vector(to_signed(512, 16)),
		std_logic_vector(to_signed(256, 16)),
		std_logic_vector(to_signed(128, 16)),
		std_logic_vector(to_signed(64, 16)),
		std_logic_vector(to_signed(32, 16)),
		std_logic_vector(to_signed(16, 16)),
		std_logic_vector(to_signed(8, 16)),
		std_logic_vector(to_signed(4, 16)),
		std_logic_vector(to_signed(2, 16)),
		std_logic_vector(to_signed(2, 16)),
		std_logic_vector(to_signed(1, 16))
	);
end lutConst;
