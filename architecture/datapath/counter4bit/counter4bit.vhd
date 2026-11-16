-- Library
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Define entity
entity counter4bit is
	port	(
				En		:		in		std_logic;							-- sinyal enable
				Res	:		in		std_logic;							-- sinyal reset
				Clk	:		in		std_logic;							-- sinyal clock
				Count	:		out	std_logic_vector (3 downto 0)	-- hasil penghitungan
			);
end counter4bit;

-- Define architecture
architecture rtl of counter4bit is
	-- sinyal penghitungan sementara
	signal	v_count	:	unsigned (3 downto 0)	:= (others => '0');
	
begin
	-- proses yang mengamati perubahan sinyal clock
	process (Clk)
	begin
		-- jika clock mengalami perubahan dan bernilai 1
		if rising_edge(Clk) then
			-- jika nilai reset adalah 1, maka hasil penghitungan menjadi 0.
			if (Res = '1') then
				v_count <= (others => '0');
			else
			-- jika nilai reset adalah 0, maka...
				-- jika nilai enable adalah 1, maka hasil penghitungan sementara ditambah 1.
				if (En = '1') then
					v_count <= v_count + 1;
				end if;
			end if;
		end if;
	end process;
	-- hasil penghitungan sementara dimasukkan ke luaran hasil penghitungan. 
	Count <= std_logic_vector(v_count);
end rtl;
		
		