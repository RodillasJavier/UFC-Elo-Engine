/**
 * frontend/src/constants/weightClasses.js
 * 
 * Constants for weight classes.
 */

/**
 * A mapping of full weight class names to their short forms.
 */
export const WC_SHORT = {
  'Heavyweight': 'HW',
  'Light Heavyweight': 'LHW',
  'Middleweight': 'MW',
  'Welterweight': 'WW',
  'Lightweight': 'LW',
  'Featherweight': 'FW',
  'Bantamweight': 'BW',
  'Flyweight': 'FLW',
  "Women's Strawweight": 'W·SW',
  "Women's Flyweight": 'W·FLW',
  "Women's Bantamweight": 'W·BW',
  "Women's Featherweight": 'W·FW',
  'Strawweight': 'SW',
  'Super Heavyweight': 'SHW',
  'Catch Weight': 'CW',
  'Open Weight': 'OW',
}

/**
 * A mapping of fight methods to their labels.
 */
export const METHOD_LABELS = {
  KO: 'KO/TKO',
  SUB: 'Submission',
  'U-DEC': 'Decision',
  'S-DEC': 'Split Dec.',
  'M-DEC': 'Maj. Dec.',
}

/**
 * Returns the short form of a weight class.
 * 
 * @param {string} wc 
 * @returns {string}
 */
export function shortenWC(wc) {
  return WC_SHORT[wc] ?? wc
}

/**
 * Returns the label for a fight method.
 * 
 * @param {string} m 
 * @returns {string}
 */
export function methodLabel(m) {
  return METHOD_LABELS[m] ?? m
}
