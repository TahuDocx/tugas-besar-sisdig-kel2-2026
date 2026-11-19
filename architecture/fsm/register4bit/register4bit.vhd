-- Nama		: Muhammad Iqbal Arsyad
-- NIM		: 33223302
-- Koordinator Asisten Praktikum Sistem Digital EL2102
-- Semester 1 Tahun Ajaran 2024/2025
-- 26 Oktober 2024
-- Percobaan 3
-- Deskripsi
-- Berfungsi untuk menyimpan nilai berukuran 4 bit. menyimpan nilai jika diaktifkan.
-- input:
--			A		data 4 bit
--			En		sinyal pengaktifan.
--			Clk	sinyal clock
--			Res	sinyal reset. Mengubah isi menjadi 0.
--	output:
--			Data	luaran data yang tersimpan.

-- Library
library ieee;
use ieee.std_logic_1164.all;

-- Define entity
entity register4bit is
	port	(
				A		:		in		std_logic_vector (3 downto 0);	-- data A
				En		:		in		std_logic;						-- sinyal Enable
				Res		:		in		std_logic;						-- sinyal Reset (sinkron, aktif tinggi)
				Clk		:		in		std_logic;						-- sinyal Clock
				Data	:		out		std_logic_vector (3 downto 0)	-- luaran data
				);
end register4bit;

-- Define architecture
architecture rtl of register4bit is
	-- sinyal untuk data yang akan disimpan. default bernilai 0.
	signal	v_data	:	std_logic_vector (3 downto 0) := x"0";

begin
	-- proses yang mengamati sinyal clock
	process (Clk)
	begin
		-- jika sinyal clock berubah dan bernilai 1
		if rising_edge(Clk) then
			-- jika sinyal reset bernilai 1 (reset sinkron, diutamakan dari enable), maka ...
			if (Res = '1') then
				-- data diubah menjadi 0.
				v_data <= x"0";
			else
				-- sinyal reset bernilai 0.
				-- jika sinyal enable bernilai 1, maka ...
				if (En = '1') then
					-- data A disimpan ke sinyal data.
					v_data <= A;
				end if;
			end if;
		end if;
	end process;
	-- sinyal data dimasukkan ke luaran Data.
	Data <= v_data;
end rtl;
