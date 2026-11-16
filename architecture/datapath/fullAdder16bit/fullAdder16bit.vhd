-- Library
library ieee;
use ieee.std_logic_1164.all;

-- Define entity
entity fullAdder16bit is
	port	(
				A, B	:		in		std_logic_vector (15 downto 0);	-- data masukan A dan B
				Cin		:		in		std_logic;								-- carry masukan
				S			:		out		std_logic_vector (15 downto 0);	-- hasil penjumlahan
				Cout	:		out		std_logic								-- carry luaran
			);
end fullAdder16bit;

-- Define architecture
architecture behavioral of fullAdder16bit is
	-- carry antar bit. v_carry(0) adalah Cin, v_carry(16) adalah Cout.
	signal v_carry	:	std_logic_vector (16 downto 0);

begin
	-- carry bit pertama berasal dari masukan Cin.
	v_carry(0) <= Cin;

	-- rangkaian ripple carry: 16 full adder, carry keluar tiap bit masuk ke bit berikutnya.
	adder : for i in 0 to 15 generate
		-- jumlah bit ke-i adalah A xor B xor carry masuk.
		S(i) <= A(i) xor B(i) xor v_carry(i);
		-- carry keluar bit ke-i bernilai 1 jika A dan B bernilai 1, atau carry masuk dan (A xor B) bernilai 1.
		v_carry(i + 1) <= (A(i) and B(i)) or (v_carry(i) and (A(i) xor B(i)));
	end generate adder;

	-- carry bit terakhir dimasukkan ke luaran Cout.
	Cout <= v_carry(16);
end behavioral;
