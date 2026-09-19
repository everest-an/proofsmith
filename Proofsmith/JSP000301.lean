/-
  Proofsmith · JSP-000301
  https://github.com/TheJustinSunPrize/awards/blob/main/problems/catalog-0301-0400.md#JSP-000301

  Problem (The Justin Sun Prize problem bank):
      "If two consecutive positive integers are powerful,
       must at least one be a perfect square?"

  Recorded resolution: NO — Solomon W. Golomb, "Powerful numbers",
  Amer. Math. Monthly 77(8) (1970), 848-852.

  Witness formalised here (the standard minimal counterexample):
      12167 = 23^3
      12168 = 2^3 * 3^2 * 13^2 = 12167 + 1
  Both are powerful; neither is a perfect square.

  Definitions (standard):
      Powerful n := every prime p dividing n satisfies p^2 | n
      IsSquare n := exists k, k * k = n
-/
import Mathlib

namespace JSP000301

/-- `n` is powerful: every prime dividing `n` divides it to at least the second power. -/
def Powerful (n : ℕ) : Prop := ∀ p : ℕ, p.Prime → p ∣ n → p ^ 2 ∣ n

/-- `n` is a perfect square. -/
def IsSquare (n : ℕ) : Prop := ∃ k : ℕ, k * k = n

/-- 12167 = 23^3 is powerful. -/
theorem powerful_12167 : Powerful 12167 := by
  intro p hp hdvd
  have hpow : p ∣ 23 ^ 3 := by
    norm_num at hdvd ⊢
    exact hdvd
  have hp23 : p ∣ 23 := hp.dvd_of_dvd_pow hpow
  rcases (Nat.dvd_prime (by norm_num : Nat.Prime 23)).mp hp23 with h1 | hpeq
  · subst h1; norm_num
  · subst hpeq; norm_num

/-- 12168 = 2^3 * 3^2 * 13^2 is powerful. -/
theorem powerful_12168 : Powerful 12168 := by
  intro p hp hdvd
  have h : p ∣ 2 ^ 3 * (3 ^ 2 * 13 ^ 2) := by
    norm_num at hdvd ⊢
    exact hdvd
  rcases (hp.dvd_mul).mp h with h2 | hrest
  · have hp2 : p ∣ 2 := hp.dvd_of_dvd_pow h2
    rcases (Nat.dvd_prime (by norm_num : Nat.Prime 2)).mp hp2 with h1 | hpeq
    · subst h1; norm_num
    · subst hpeq; norm_num
  · rcases (hp.dvd_mul).mp hrest with h3 | h13
    · have hp3 : p ∣ 3 := hp.dvd_of_dvd_pow h3
      rcases (Nat.dvd_prime (by norm_num : Nat.Prime 3)).mp hp3 with h1 | hpeq
      · subst h1; norm_num
      · subst hpeq; norm_num
    · have hp13 : p ∣ 13 := hp.dvd_of_dvd_pow h13
      rcases (Nat.dvd_prime (by norm_num : Nat.Prime 13)).mp hp13 with h1 | hpeq
      · subst h1; norm_num
      · subst hpeq; norm_num

/-- 12167 is not a perfect square. -/
theorem not_square_12167 : ¬ IsSquare 12167 := by
  rintro ⟨k, hk⟩
  have hk_le : k ≤ 110 := by
    by_contra h
    have h111 : 111 ≤ k := by omega
    nlinarith
  interval_cases k <;> norm_num at hk

/-- 12168 is not a perfect square. -/
theorem not_square_12168 : ¬ IsSquare 12168 := by
  rintro ⟨k, hk⟩
  have hk_le : k ≤ 110 := by
    by_contra h
    have h111 : 111 ≤ k := by omega
    nlinarith
  interval_cases k <;> norm_num at hk

/-- **JSP-000301**: it is *not* the case that of two consecutive powerful
positive integers at least one must be a perfect square. -/
theorem jsp_000301 :
    ¬ (∀ n : ℕ, 0 < n → Powerful n → Powerful (n + 1) →
        IsSquare n ∨ IsSquare (n + 1)) := by
  intro h
  have hc := h 12167 (by norm_num) powerful_12167 powerful_12168
  rcases hc with hsq | hsq
  · exact not_square_12167 hsq
  · exact not_square_12168 hsq

end JSP000301
