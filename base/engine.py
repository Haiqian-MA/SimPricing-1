import time
import numpy as np
import numba as nb

from collections.abc import Iterable


@nb.jit(nopython=True)
def _fast_sim_loop_geo_brownian(s_0, n_dim, t_diff, sigma_array, r, epsilon):
    prc = []
    s_array = np.array([s_0, ] * n_dim)

    for t, i in zip(t_diff, range(t_diff.shape[0])):
        epsilon_current = np.array(list(epsilon[:, i]))
        s_array = s_array * np.exp((r - np.power(sigma_array, 2) / 2) * t
                                   + sigma_array * epsilon_current * np.sqrt(t))
        prc.append(s_array)

    return prc


class SimEngine(object):
    def __init__(self, method="GeoBrownian", s_0=100, **kwargs):
        """
        Currently support methods:
            GeoBrownian: Geometric Brownian Motion
        kwargs for:
            GeoBrownian: {"sigma": standard deviation, float or iterable
                          "r": risk-free expected payoff, float
                          "rho": correlation matrix, numpy.matrix
                          }
        :param method:    Type: String        To specify the method for generating price sequence.
        :param s_0:       Type: int or float  initial price of underlying asset
        :param kwargs:    Type: Dict
        """
        full_methods = ["GeoBrownian", ]
        full_kwarg_map = {"GeoBrownian": ["sigma", "r", "rho", ], }

        if method not in full_methods:
            raise ValueError("Illegal input of method!")

        for key in kwargs.keys():
            if key not in full_kwarg_map[method]:
                raise ValueError("Illegal input of kwargs!")

        self._method = method
        self._kwargs = kwargs
        self._s_0 = float(s_0)
        self._n_dim = None

        self._time_1 = None
        self._time_2 = None

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def s_0(self):
        return self._s_0

    @property
    def n_dim(self):
        if self._method == "GeoBrownian":
            if isinstance(self.kwargs["sigma"], list):
                return len(self.kwargs["sigma"])
            else:
                return 1
        else:
            raise ValueError

    @property
    def time_1(self):
        return self._time_1

    @property
    def time_2(self):
        return self._time_2

    def prc_generator(self, upper_t):
        """
        Generate price based on upper_t. Must keep in mind that upper_t is expressed in Year.
        :param upper_t:     Type: float or iterable   expressed in Year
        :return:            Type: numpy.array   matched with upper_t
        """
        tic = time.time()

        if not isinstance(upper_t, Iterable):
            upper_t = [upper_t, ]

        if self._method == "GeoBrownian":

            sigma_raw = self.kwargs["sigma"]
            sigma_array = np.array(sigma_raw if isinstance(sigma_raw, Iterable) else [sigma_raw, ])

            r = self.kwargs["r"]

            t_diff = np.diff(upper_t, prepend=0)

            if self.n_dim > 1:
                rho = self.kwargs["rho"]
                upper_r = np.linalg.cholesky(rho)

                if not isinstance(rho, np.matrix):
                    raise ValueError("Illegal input type of rho")

                if rho.shape[0] != rho.shape[1] or rho.shape[0] != self.n_dim:
                    raise ValueError("Illegal input dimension of rho")
            else:
                upper_r = 1

            x = np.random.normal(0, 1, [self.n_dim, t_diff.shape[0]])
            epsilon = upper_r * x

            self._time_1 = time.time() - tic
            tic = time.time()

            prc = _fast_sim_loop_geo_brownian(self.s_0, self.n_dim, t_diff, sigma_array, r, epsilon)
            prc = np.array(prc)

            self._time_2 = time.time() - tic
        else:
            raise ValueError

        return prc


if __name__ == "__main__":
    rho_ = np.matrix([[1, 0.5], [0.5, 1]])
    sigma_ = [0.2, 0.2]

    # sigma_ = 0.4

    tic_ = time.time()
    time_1_l = []
    time_2_l = []

    upper_t_ = range(1, 81, 1)
    upper_t_ = np.array(upper_t_) / 252

    for _ in range(50000):
        sim_engine = SimEngine(method="GeoBrownian", sigma=sigma_, r=0.03, rho=rho_)

        prc_seq = sim_engine.prc_generator(upper_t=upper_t_)
        time_1_l.append(sim_engine.time_1)
        time_2_l.append(sim_engine.time_2)

    toc = time.time() - tic_
    print(toc)

    print(sum(time_1_l))
    print(sum(time_2_l))


    # print(np.corrcoef(prc_seq[:, 0], prc_seq[:, 1]))
    # import matplotlib.pyplot as plt
    #
    # plt.plot(prc_seq)
    # plt.show()



