-- Library
library ieee;
use ieee.std_logic_1164.all;

-- Define entity
entity flipFlop is
	port	(
				D		:		in		std_logic;	-- data masukan D
				En		:		in		std_logic;	-- sinyal Enable
				Res		:		in		std_logic;	-- sinyal Reset (sinkron, aktif tinggi)
				Clk		:		in		std_logic;	-- sinyal Clock
				Q		:		out		std_logic;	-- luaran data
				Qbar	:		out		std_logic	-- luaran komplemen data
				);
end flipFlop;

-- Define architecture
architecture rtl of flipFlop is
	-- sinyal untuk data yang akan disimpan. default bernilai 0.
	signal	v_data	:	std_logic := '0';

begin
	-- proses yang mengamati sinyal clock
	process (Clk)
	begin
		-- jika sinyal clock berubah dan bernilai 1
		if rising_edge(Clk) then
			-- jika sinyal reset bernilai 1 (reset sinkron, diutamakan dari enable), maka ...
			if (Res = '1') then
				-- data diubah menjadi 0.
				v_data <= '0';
			else
				-- sinyal reset bernilai 0.
				-- jika sinyal enable bernilai 1, maka ...
				if (En = '1') then
					-- data D disimpan ke sinyal data.
					v_data <= D;
				end if;
			end if;
		end if;
	end process;
	-- sinyal data dimasukkan ke luaran Q.
	Q <= v_data;
	-- komplemen sinyal data dimasukkan ke luaran Qbar.
	Qbar <= not v_data;
end rtl;
