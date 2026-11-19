-- Library
library ieee;
use ieee.std_logic_1164.all;

-- Define entity
entity mux16bit2to1 is
	port	(
				A		  :		in		std_logic_vector (15 downto 0);	-- data A, dipilih saat S = '0'
				B		  :		in		std_logic_vector (15 downto 0);	-- data B, dipilih saat S = '1'
				Sel	  :		in		std_logic;							-- sinyal pemilih
				Data	:		out		std_logic_vector (15 downto 0)		-- luaran data terpilih
				);
end mux16bit2to1;

-- Define architecture
architecture behavioral of mux16bit2to1 is
begin
	-- jika S bernilai 0, maka A diteruskan ke luaran. selain itu, B diteruskan.
	with Sel select
		Data <=	A	when '0',
					B	when others;
end behavioral;
