-- Library
library ieee;
use ieee.std_logic_1164.all;

-- Define entity
entity shifter16bit is
	port	(
				A		:		in		std_logic_vector (15 downto 0);	-- data A (bertanda, Q2.14)
				S		:		in		std_logic_vector (3 downto 0);		-- jumlah geser ke kanan (0-15)
				Data	:		out		std_logic_vector (15 downto 0)		-- luaran data, A digeser S bit
				);
end shifter16bit;

-- Define architecture
architecture behavioral of shifter16bit is
	-- sinyal berisi salinan bit tanda A(15) untuk mengisi bit kiri yang kosong.
	signal	v_sign	:	std_logic_vector (15 downto 0);

begin
	-- bit tanda A disalin ke seluruh bit v_sign.
	v_sign <= (others => A(15));

	-- geser kanan aritmetika: A digeser S bit ke kanan, bit kiri diisi bit tanda
	-- agar nilai negatif tetap negatif (sama dengan v >> s di cordic.py).
	-- S = x"F" dan nilai S tak terdefinisi masuk ke cabang others.
	with S select
		Data <=	A											when x"0",
					v_sign(0 downto 0)	& A(15 downto 1)		when x"1",
					v_sign(1 downto 0)	& A(15 downto 2)		when x"2",
					v_sign(2 downto 0)	& A(15 downto 3)		when x"3",
					v_sign(3 downto 0)	& A(15 downto 4)		when x"4",
					v_sign(4 downto 0)	& A(15 downto 5)		when x"5",
					v_sign(5 downto 0)	& A(15 downto 6)		when x"6",
					v_sign(6 downto 0)	& A(15 downto 7)		when x"7",
					v_sign(7 downto 0)	& A(15 downto 8)		when x"8",
					v_sign(8 downto 0)	& A(15 downto 9)		when x"9",
					v_sign(9 downto 0)	& A(15 downto 10)		when x"A",
					v_sign(10 downto 0)	& A(15 downto 11)		when x"B",
					v_sign(11 downto 0)	& A(15 downto 12)		when x"C",
					v_sign(12 downto 0)	& A(15 downto 13)		when x"D",
					v_sign(13 downto 0)	& A(15 downto 14)		when x"E",
					v_sign(14 downto 0)	& A(15 downto 15)		when others;
end behavioral;
