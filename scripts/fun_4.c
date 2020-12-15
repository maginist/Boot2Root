#include <stdio.h>
#include <stdlib.h>

int func4(int nb)
{
	static int tmp;

	if (nb <= 1)
		return(1);
	tmp = func4(nb-1);
	tmp = tmp + func4(nb-2);
	return (tmp);
}


int main(int ac, char **av)
{
	int nb;

	nb = atoi(av[1]);
	nb = func4(nb);
	printf("%d\n", nb);
}