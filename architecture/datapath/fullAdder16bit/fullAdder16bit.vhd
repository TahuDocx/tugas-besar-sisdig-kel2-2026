LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;


ENTITY fullAdder16bit IS 
	PORT(
		A, B 	: IN STD_LOGIC_VECTOR(15 DOWNTO 0);
		Cin 	: IN STD_LOGIC;
		S		: OUT STD_LOGIC_VECTOR(15 DOWNTO 0);
		Cout	: OUT STD_LOGIC
	);
END fullAdder16bit;


ARCHITECTURE behavioral OF fullAdder16bit IS
	SIGNAL C1, C2, C3, C4, C5, C6, C7, C8 : STD_LOGIC;
   SIGNAL C9, C10, C11, C12, C13, C14, C15 : STD_LOGIC;

BEGIN
	 S(0)  <= A(0) XOR B(0) XOR Cin;
    C1    <= (A(0) AND B(0)) OR (Cin AND (A(0) XOR B(0)));

    S(1)  <= A(1) XOR B(1) XOR C1;
    C2    <= (A(1) AND B(1)) OR (C1 AND (A(1) XOR B(1)));

    S(2)  <= A(2) XOR B(2) XOR C2;
    C3    <= (A(2) AND B(2)) OR (C2 AND (A(2) XOR B(2)));

    S(3)  <= A(3) XOR B(3) XOR C3;
    C4    <= (A(3) AND B(3)) OR (C3 AND (A(3) XOR B(3)));

    S(4)  <= A(4) XOR B(4) XOR C4;
    C5    <= (A(4) AND B(4)) OR (C4 AND (A(4) XOR B(4)));

    S(5)  <= A(5) XOR B(5) XOR C5;
    C6    <= (A(5) AND B(5)) OR (C5 AND (A(5) XOR B(5)));

    S(6)  <= A(6) XOR B(6) XOR C6;
    C7    <= (A(6) AND B(6)) OR (C6 AND (A(6) XOR B(6)));

    S(7)  <= A(7) XOR B(7) XOR C7;
    C8    <= (A(7) AND B(7)) OR (C7 AND (A(7) XOR B(7)));

    S(8)  <= A(8) XOR B(8) XOR C8;
    C9    <= (A(8) AND B(8)) OR (C8 AND (A(8) XOR B(8)));

    S(9)  <= A(9) XOR B(9) XOR C9;
    C10   <= (A(9) AND B(9)) OR (C9 AND (A(9) XOR B(9)));

    S(10) <= A(10) XOR B(10) XOR C10;
    C11   <= (A(10) AND B(10)) OR (C10 AND (A(10) XOR B(10)));

    S(11) <= A(11) XOR B(11) XOR C11;
    C12   <= (A(11) AND B(11)) OR (C11 AND (A(11) XOR B(11)));

    S(12) <= A(12) XOR B(12) XOR C12;
    C13   <= (A(12) AND B(12)) OR (C12 AND (A(12) XOR B(12)));

    S(13) <= A(13) XOR B(13) XOR C13;
    C14   <= (A(13) AND B(13)) OR (C13 AND (A(13) XOR B(13)));

    S(14) <= A(14) XOR B(14) XOR C14;
    C15   <= (A(14) AND B(14)) OR (C14 AND (A(14) XOR B(14)));

    S(15) <= A(15) XOR B(15) XOR C15;
    Cout  <= (A(15) AND B(15)) OR (C15 AND (A(15) XOR B(15)));

END behavioral;