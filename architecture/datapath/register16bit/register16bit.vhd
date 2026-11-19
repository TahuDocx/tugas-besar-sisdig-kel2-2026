-- Library
library ieee;
use ieee.std_logic_1164.all;

-- Define entity
entity register16bit is
	port	(
				A		:		in		std_logic_vector (15 downto 0);	-- data A
				En		:		in		std_logic;						-- sinyal Enable
				Res		:		in		std_logic;						-- sinyal Reset (sinkron, aktif tinggi)
				Clk		:		in		std_logic;						-- sinyal Clock
				Data	:		out		std_logic_vector (15 downto 0)	-- luaran data
				);
end register16bit;

-- Define architecture
architecture rtl of register16bit is
	-- sinyal untuk data yang akan disimpan. default bernilai 0.
	signal	v_data	:	std_logic_vector (15 downto 0) := x"0000";

begin
	-- proses yang mengamati sinyal clock
	process (Clk)
	begin
		-- jika sinyal clock berubah dan bernilai 1
		if rising_edge(Clk) then
			-- jika sinyal reset bernilai 1 (reset sinkron, diutamakan dari enable), maka ...
			if (Res = '1') then
				-- data diubah menjadi 0.
				v_data <= x"0000";
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
