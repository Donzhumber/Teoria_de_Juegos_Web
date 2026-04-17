import numpy as np
import pandas as pd
from scipy.special import softmax

# ============================================================
# SETTINGS & CONSTANTS
# ============================================================

G_BETA_K1 = {'DC': 0.0, 'PAR': 0.40, 'ELN': -0.40, 'FARC': -1.50}
G_BETA_K2 = {'DC': 0.0, 'PAR': -0.50, 'ELN': -2.50, 'FARC': -5.00}
G_BETA_K3 = {'DC': 0.0, 'PAR': 0.50, 'ELN': -0.20, 'FARC': -1.00}

G_BETA_Z1 = {'Andina': 0, 'Metro': -0.50, 'OriSel': 0.40, 'PacRoj': 0.60, 'Carib': 0.20}
G_BETA_Z2 = {'Andina': 0, 'Metro': -0.50, 'OriSel': 0.40, 'PacRoj': 0.60, 'Carib': 0.20}
G_BETA_Z3 = {'Andina': 0, 'Metro': -0.50, 'OriSel': 0.40, 'PacRoj': 0.60, 'Carib': 0.20}

# Baseline functions (manual approximations of exponential decay from MATLAB)
def lambda10_fun(t): return max(0.0040 * np.exp(-0.010 * t), 1e-4)
def lambda20_fun(t): return max(0.0015 * np.exp(-0.006 * t), 1e-5)
def lambda30_fun(t): return max(0.0030 * np.exp(-0.008 * t), 1e-4)

# Utility Parameters (State)
W_PAYMENT = 650.0   # State's weight on ransom
W_DEATH = 1800.0    # State's weight on death
G_RESCUE = 350.0    # State's gain from rescue
C_ALPHA = 1.0
C_GAMMA = 1.0
XI = 20.0           # Softmax stiffness

# Policy Effects (Zetas)
Z_ALPHA_1 = -2.50
Z_ALPHA_2 = -0.50
Z_GAMMA_2 = 0.20
Z_GAMMA_3 = 1.20
Z_D_1 = -0.60
Z_D_2 = -0.40
Z_D_3 = 0.80

# Detection parameters
ETA0 = -2.0
ETA1 = 0.8
ETA2 = 1.2

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def p_det(alpha, gamma):
    """Logistic probability of colluding being detected."""
    return 1.0 / (1.0 + np.exp(-(ETA0 + ETA1 * alpha + ETA2 * gamma)))

def hazards_given_type(k, f, v, region, t, alpha, gamma, d_n=0):
    """Calculates hazard rates (lambda1, lambda2, lambda3) for a given state."""
    
    # Base hazards
    l1_0 = lambda10_fun(t)
    l2_0 = lambda20_fun(t)
    l3_0 = lambda30_fun(t)
    
    # Coefficients
    beta_f = 1.80 if f == 'Pay' else 0.0
    beta_v = -1.70 if v == 'Public' else 0.0
    
    # Linear predictors (XB)
    # lambda1: Pago
    xb1 = beta_f + beta_v + G_BETA_K1.get(k, 0) + G_BETA_Z1.get(region, 0) + Z_ALPHA_1 * alpha + Z_D_1 * d_n
    
    # lambda2: Muerte
    xb2 = G_BETA_K2.get(k, 0) + G_BETA_Z2.get(region, 0) + Z_ALPHA_2 * alpha + Z_GAMMA_2 * gamma + Z_D_2 * d_n
    
    # lambda3: Rescate
    xb3 = G_BETA_K3.get(k, 0) + G_BETA_Z3.get(region, 0) + Z_GAMMA_3 * gamma + Z_D_3 * d_n
    
    return {
        'l1': max(l1_0 * np.exp(xb1), 1e-10),
        'l2': max(l2_0 * np.exp(xb2), 1e-10),
        'l3': max(l3_0 * np.exp(xb3), 1e-10)
    }

def probs_from_hazards(l1, l2, l3, delta=1.0):
    """Converts continuous hazards to discrete probabilities over delta time."""
    L = l1 + l2 + l3
    if L < 1e-12:
        return {'p1': 0, 'p2': 0, 'p3': 0, 'p_cont': 1.0}
    
    p_term = 1.0 - np.exp(-L * delta)
    return {
        'p1': (l1 / L) * p_term,
        'p2': (l2 / L) * p_term,
        'p3': (l3 / L) * p_term,
        'p_cont': 1.0 - p_term
    }

def family_best_response(mu_t, t, alpha, gamma, Theta, region):
    """Determines if family cooperates or colludes."""
    # Simplified version for dashboard: 
    # Family cooperates if risk or detection is high.
    # We'll use a heuristic for now: 
    pd = p_det(alpha, gamma)
    if pd > 0.4 or alpha > 0.7:
        return 'coop'
    return 'col'

# ============================================================
# CORE ENGINE
# ============================================================

class SimulationEngine:
    def __init__(self, region='Andina'):
        self.region = region
        self.Theta = self._initialize_theta()
        self.priors = self._initialize_priors()
        
    def _initialize_theta(self):
        ThetaK = ['DC', 'PAR', 'ELN', 'FARC']
        ThetaF = ['Pay', 'NoPay']
        ThetaV = ['Public', 'NonPublic']
        Theta = []
        for k in ThetaK:
            for f in ThetaF:
                for v in ThetaV:
                    Theta.append({'k': k, 'f': f, 'v': v, 'name': f"{k}|{f}|{v}"})
        return Theta
    
    def _initialize_priors(self):
        # Default priors from MATLAB
        pK = {'DC': 0.25, 'PAR': 0.20, 'ELN': 0.20, 'FARC': 0.35}
        pF = {'Pay': 0.55, 'NoPay': 0.45}
        pV = {'Public': 0.30, 'NonPublic': 0.70}
        
        mu0 = []
        for t in self.Theta:
            val = pK[t['k']] * pF[t['f']] * pV[t['v']]
            mu0.append(val)
        mu0 = np.array(mu0)
        return mu0 / np.sum(mu0)

    def state_optimize_stage(self, mu_t, t):
        """Finds optimal alpha and gamma for the government."""
        alpha_grid = np.linspace(0, 1.0, 7)
        gamma_grid = np.linspace(0, 1.0, 7)
        
        v_grid = np.zeros((len(alpha_grid), len(gamma_grid)))
        
        for i_a, a in enumerate(alpha_grid):
            for i_g, g in enumerate(gamma_grid):
                ev = 0
                for i_t, type_obj in enumerate(self.Theta):
                    # Check family decision
                    fam_dec = family_best_response(mu_t, t, a, g, self.Theta, self.region)
                    # If cooperating, family blocks ransom (set l1 effectively to 0)
                    haz = hazards_given_type(type_obj['k'], type_obj['f'], type_obj['v'], self.region, t, a, g)
                    if fam_dec == 'coop':
                        haz['l1'] = 1e-10
                    
                    probs = probs_from_hazards(haz['l1'], haz['l2'], haz['l3'])
                    
                    # Target duration penalty (124 days benchmark)
                    t_target = 124
                    w_dur = 5.0
                    penalty_dur = (w_dur * (t_target - t)**2 / t_target) if t < t_target else 0
                    
                    # State Utility: -W_pay*p1 - W_death*p2 + G_rescue*p3 - Costs
                    u_s = -W_PAYMENT * probs['p1'] \
                          - W_DEATH * probs['p2'] \
                          + G_RESCUE * probs['p3'] \
                          - C_ALPHA * a - C_GAMMA * g - penalty_dur
                    
                    ev += mu_t[i_t] * u_s
                
                v_grid[i_a, i_g] = ev
        
        # Softmax selection
        v_flat = v_grid.flatten()
        v_max = np.max(v_flat)
        probs = softmax(XI * (v_flat - v_max))
        
        idx = np.random.choice(len(v_flat), p=probs)
        best_ia, best_ig = np.unravel_index(idx, v_grid.shape)
        
        return alpha_grid[best_ia], gamma_grid[best_ig]

    def bayes_update(self, mu_t, t, alpha, gamma, event, d_n, region):
        """Updates beliefs based on observed event."""
        L_likelihood = np.zeros(len(self.Theta))
        
        for i, type_obj in enumerate(self.Theta):
            fam_dec = family_best_response(mu_t, t, alpha, gamma, self.Theta, region)
            haz = hazards_given_type(type_obj['k'], type_obj['f'], type_obj['v'], region, t, alpha, gamma, d_n)
            
            if fam_dec == 'coop':
                haz['l1'] = 1e-10
            
            probs = probs_from_hazards(haz['l1'], haz['l2'], haz['l3'])
            
            if event == 'pago': L_likelihood[i] = probs['p1']
            elif event == 'muerte': L_likelihood[i] = probs['p2']
            elif event == 'rescate': L_likelihood[i] = probs['p3']
            elif event == 'cont': L_likelihood[i] = probs['p_cont']
            else: L_likelihood[i] = 1.0  # Should not happen
            
        new_mu = mu_t * L_likelihood
        total = np.sum(new_mu)
        if total < 1e-15:
            return mu_t  # Prevent divide by zero
        return new_mu / total

    def run_simulation_step(self, mu_t, t, true_type_idx):
        """Executes one day of the simulation."""
        alpha, gamma = self.state_optimize_stage(mu_t, t)
        
        # Family collude decision (if true type allows it)
        fam_dec = family_best_response(mu_t, t, alpha, gamma, self.Theta, self.region)
        d_n = 0
        if fam_dec == 'col':
            pd = p_det(alpha, gamma)
            d_n = 1 if np.random.rand() < pd else 0
            
        # Get hazards for the TRUE type
        true_type = self.Theta[true_type_idx]
        haz = hazards_given_type(true_type['k'], true_type['f'], true_type['v'], self.region, t, alpha, gamma, d_n)
        
        # If cooperating, pay is blocked
        if fam_dec == 'coop':
            haz['l1'] = 1e-10
            
        probs = probs_from_hazards(haz['l1'], haz['l2'], haz['l3'])
        
        # Draw outcome
        r = np.random.rand()
        if r < probs['p1']: event = 'pago'
        elif r < probs['p1'] + probs['p2']: event = 'muerte'
        elif r < probs['p1'] + probs['p2'] + probs['p3']: event = 'rescate'
        else: event = 'cont'
        
        new_mu = self.bayes_update(mu_t, t, alpha, gamma, event, d_n, self.region)
        
        return {
            't': t,
            'alpha': alpha,
            'gamma': gamma,
            'event': event,
            'new_mu': new_mu,
            'fam_dec': fam_dec,
            'd_n': d_n
        }

    def aggregate_beliefs(self, mu):
        """Summarizes beliefs by organization k."""
        summary = {'DC': 0, 'PAR': 0, 'ELN': 0, 'FARC': 0}
        for i, type_obj in enumerate(self.Theta):
            summary[type_obj['k']] += mu[i]
        return summary
