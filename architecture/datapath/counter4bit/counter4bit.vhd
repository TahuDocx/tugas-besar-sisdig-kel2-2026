-- Library
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Define entity
entity counter4bit is
	port	(
				En		:		in		std_logic;						-- sinyal enable
				Res		:		in		std_logic;						-- sinyal reset (sinkron, aktif tinggi)
				Clk		:		in		std_logic;						-- sinyal clock
				Count	:		out		std_logic_vector (3 downto 0)	-- hasil penghitungan
				);
end counter4bit;

-- Define architecture
architecture rtl of counter4bit is
	-- sinyal penghitungan sementara
	signal	v_count	:	unsigned (3 downto 0)	:= (others => '0');

begin
	-- proses yang mengamati sinyal clock
	process (Clk)
	begin
		-- jika sinyal clock berubah dan bernilai 1
		if rising_edge(Clk) then
			-- jika sinyal reset bernilai 1 (reset sinkron, diutamakan dari enable), maka ...
			if (Res = '1') then
				-- hasil penghitungan menjadi 0.
				v_count <= (others => '0');
			else
				-- sinyal reset bernilai 0.
				-- jika sinyal enable bernilai 1, maka ...
				if (En = '1') then
					-- hasil penghitungan sementara ditambah 1.
					v_count <= v_count + 1;
				end if;
			end if;
		end if;
	end process;
	-- hasil penghitungan sementara dimasukkan ke luaran hasil penghitungan.
	Count <= std_logic_vector(v_count);
end rtl;
