import asyncio
import random
import datetime
'''
this is my attempt of (poorly) simulating that famous NKODICE on steam and add it as a function of my bot.
what I mean by poorly is that lots of features in the real game was stripped in this simulation.
if anyone sees this file, plz go support the real game! https://store.steampowered.com/app/1510950/NKODICE/
'''


class fake_nkodice:

    def __init__(self, player_id):
        self.player_id = player_id
        self.U_score = 0
        self.M_score = 0
        self.C_score = 0
        self.total_score = 0
        self.combo_count = 0

        self.U_score_add = 0
        self.M_score_add = 0
        self.C_score_add = 0

        self.OM_combo = 1
        self.M_combo = 1
        self.C_combo = 1
        self.CH_combo = 1
        self.UN_combo = 1
        self.UT_combo = 1
        self.OCH_combo = 1

        self.chances = 5
        self.nudges_available = 5

        self.chances_left = self.chances
        self.nudges_left = self.nudges_available
        self.rolls = 0
        self.nudges = 0

        self.pool = ['う', 'ま', 'ち', 'ん', 'こ', 'お']
        self.selection = ['', '', '', '', '']
        self.temp_selection = []  # for combo calculation
        self.dices = 5
        self.last_appeared_words = []
        self.appeared_words = []

        self.ochinchin = False
        self.nnn = False
        self.ooo = False

        self.ochinchin_count = 0
        self.word_count = 0

        self.selection_disp = ''
        self.basic_stat = ''
        self.combo_stat = ''
        self.consecutive_stat = ''
        self.bonus_stat = 'NO BONUS'
        self.status_disp = ''

    def reset(self):
        self.chances_left -= 1
        self.rolls += 1
        self.selection = []
        self.combo_count = 0
        self.U_score_add = 0
        self.M_score_add = 0
        self.C_score_add = 0
        self.ochinchin = False
        self.nnn = False
        self.ooo = False
        self.basic_stat = ''
        self.combo_stat = ''
        self.consecutive_stat = ''
        self.bonus_stat = ''
        self.status_disp = ''
        self.appeared_words = []

    def roll(self):
        self.reset()
        for i in range(self.dices):
            self.selection.append(random.choice(self.pool))
        if self.nudges_left > 0:
            self.status_disp = 'PRESS ⏫ TO NUDGE OR WAIT ...\n'
        # print(f"self.selection: {self.selection}")

    async def nudge(self):
        if self.nudges_left > 0:
            j = random.randint(1, self.dices)
            for i in range(j):
                self.selection[random.randint(0, len(self.selection) - 1)] = random.choice(self.pool)
            self.nudges += 1
            self.nudges_left -= 1
            if self.nudges_left < 0:
                self.nudges_left = 0

    async def score_calc(self):
        # clear status message and combo stats
        self.status_disp= ''
        # begin score calculation
        # calculate basic score
        for item in self.selection:
            if item == 'う':
                self.U_score_add += 500
            if item == 'ま':
                self.M_score_add += 500
            if item == 'ち':
                self.C_score_add += 500
            if item == 'ん':
                self.U_score_add += 50
                self.M_score_add += 50
                self.C_score_add += 50
            if item == 'こ':
                self.U_score_add += 100
                self.M_score_add += 100
                self.C_score_add += 100
            if item == 'お':
                self.U_score_add += 300
                self.M_score_add += 300
                self.C_score_add += 300

        self.basic_stat += f'🇺 + {self.U_score_add}\000\000 🇲 + {self.M_score_add}\000\000 🇨 + {self.C_score_add}\n'

        # check for combos
        # most combos ends with n, ko so check these ones first
        if 'ん' in self.selection and 'こ' in self.selection:
            if 'ま' in self.selection:  # manko / omanko
                if 'お' in self.selection:
                    self.appeared_words.append('OM')
                else:
                    self.appeared_words.append('M')
            if 'ち' in self.selection:  # chinko
                self.appeared_words.append('C')
            if 'う' in self.selection:  # unko
                self.appeared_words.append('UN')

        if 'ん' in self.selection and 'ち' in self.selection:
            if 'う' in self.selection:  # unchi
                self.appeared_words.append('UT')
            # chinchin and ochinchin
            self.temp_selection = self.selection[:]
            self.temp_selection.remove('ち')
            self.temp_selection.remove('ん')
            if 'ち' in self.temp_selection and 'ん' in self.temp_selection:
                if 'お' in self.temp_selection:
                    self.appeared_words.append('OCH')
                else:
                    self.appeared_words.append('CH')

        for item in self.appeared_words:
            if item == 'UN':
                self.UN_combo = self.UN_combo + 1 if 'UN' in self.last_appeared_words else 1
                self.combo_stat += f'[ＵＮＫＯ] 🇺 + {1000 * self.UN_combo} ({self.UN_combo}x)\n'
                self.U_score_add += 1000 * self.UN_combo
                self.combo_count += 1
            if item == 'UT':
                self.combo_stat += f'[ＵＮＣＨＩ] 🇺 + {1000 * self.UT_combo} ({self.UT_combo}x)\n'
                self.U_score_add += 1000 * self.UT_combo
                self.combo_count += 1
            if item == 'OM':
                self.OM_combo = self.OM_combo + 1 if 'OM' in self.last_appeared_words else 1
                self.combo_stat += f'[ＯＭＡＮＫＯ] 🇲 + {5000 * self.OM_combo} ({self.OM_combo}x)\n'
                self.M_score_add += 5000 * self.OM_combo
                self.combo_count += 1
            if item == 'M':
                self.M_combo = self.M_combo + 1 if 'M' in self.last_appeared_words else 1
                self.combo_stat += f'[ＭＡＮＫＯ] 🇲 + {1000 * self.M_combo} ({self.M_combo}x)\n'
                self.M_score_add += 1000 * self.M_combo
                self.combo_count += 1
            if item == 'CH':
                self.CH_combo = self.CH_combo + 1 if 'CH' in self.last_appeared_words else 1
                self.combo_stat += f'[ＣＨＩＮＣＨＩＮ] 🇨 + {3000 * self.CH_combo} ({self.CH_combo}x)\n'
                self.C_score_add += 3000 * self.CH_combo
                self.combo_count += 1
            if item == 'C':
                self.C_combo = self.C_combo + 1 if 'C' in self.last_appeared_words else 1
                self.combo_stat += f'[ＣＨＩＮＫＯ] 🇨 + {1000 * self.C_combo} ({self.C_combo}x)\n'
                self.C_score_add += 1000 * self.C_combo
                self.combo_count += 1
            if item == 'OCH':
                self.OCH_combo = self.OCH_combo + 1 if 'OCH' in self.last_appeared_words else 1
                self.combo_stat += f'🔸**[!!!ＯＣＨＩＮＣＨＩＮ!!!]**🔸 🇨 + {10000 * self.OCH_combo} ({self.OCH_combo}x)\n'
                self.C_score_add += 10000 * self.OCH_combo
                self.combo_count += 1
                self.ochinchin = True
                self.ochinchin_count += 1

        self.last_appeared_words = self.appeared_words[:]  # store the appeared words of this round

        # check for consecutive occurrences
        if self.selection.count('う') >= 3:
            self.U_score_add *= (2 + (self.selection.count('う') - 3))
            self.consecutive_stat += f"[{'Ｕ' * self.selection.count('う')}] 🇺 × {(2 + (self.selection.count('う') - 3))}\n"
        if self.selection.count('ま') >= 3:
            self.M_score_add *= (2 + (self.selection.count('ま') - 3))
            self.consecutive_stat += f"[{'Ｍ' * self.selection.count('ま')}] 🇲 × {(2 + (self.selection.count('ま') - 3))}\n"
        if self.selection.count('ち') >= 3:
            self.C_score_add *= (2 + (self.selection.count('ち') - 3))
            self.consecutive_stat += f"[{'Ｃ' * self.selection.count('ち')}] 🇨 × {(2 + (self.selection.count('ち') - 3))}\n"
        if self.selection.count('ん') >= 3:
            self.U_score_add = -(self.U_score_add * (3 + (self.selection.count('ん') - 3)))
            self.M_score_add = -(self.M_score_add * (3 + (self.selection.count('ん') - 3)))
            self.C_score_add = -(self.C_score_add * (3 + (self.selection.count('ん') - 3)))
            self.consecutive_stat += f"[{'Ｎ' * self.selection.count('ん')}] 🇺 🇲 🇨 × {(-3 - (self.selection.count('ん') - 3))}\n"
            self.nnn = True
        if self.selection.count('こ') >= 3:
            self.U_score_add *= (1.5 + (self.selection.count('こ') - 3))
            self.M_score_add *= (1.5 + (self.selection.count('こ') - 3))
            self.C_score_add *= (1.5 + (self.selection.count('こ') - 3))
            self.consecutive_stat += f"[{'Ｋ' * self.selection.count('こ')}] 🇺 🇲 🇨 × {(1.5 + (self.selection.count('こ') - 3))}\n"
        if self.selection.count('お') >= 3:
            self.U_score_add = int(self.U_score_add) * (1.5 + (self.selection.count('お') - 3))
            self.M_score_add = int(self.M_score_add) * (1.5 + (self.selection.count('お') - 3))
            self.C_score_add = int(self.C_score_add) * (1.5 + (self.selection.count('お') - 3))
            self.consecutive_stat += f"[{'Ｏ' * self.selection.count('お')}] 🇺 🇲 🇨 × {(1.5 + (self.selection.count('お') - 3))}\n"
            self.ooo = True

        self.U_score += self.U_score_add
        self.M_score += self.M_score_add
        self.C_score += self.C_score_add
        '''
        if self.ooo:
            self.U_score = abs(self.U_score)
            self.M_score = abs(self.M_score)
            self.C_score = abs(self.C_score)
        if self.nnn:
            self.U_score = -abs(self.U_score)
            self.M_score = -abs(self.M_score)
            self.C_score = -abs(self.C_score)
        '''

        self.total_score = self.M_score + self.C_score + self.U_score
        self.word_count += self.combo_count

        self.give_bonus()
        self.status_disp = '-\n'.join([self.basic_stat, self.combo_stat, self.consecutive_stat, self.bonus_stat])

    # give extra roll if any combos appeared
    def give_bonus(self):
        self.dices = 5  # reset number of dices to 5 anyways, otherwise the game would be too long
        if self.ochinchin:
            self.dices = 10
            self.bonus_stat += f'{self.dices} DICE FOR NEXT ROUND\n'
        if self.combo_count >= 2:
            extra_dices = self.combo_count - 1
            self.dices += extra_dices
            if self.dices >= 10:
                self.dices = 10
            if not self.ochinchin:
                self.bonus_stat += f'{self.dices} DICE FOR NEXT ROUND\n'
        if self.combo_count >= 1:
            self.chances_left += 1
            self.bonus_stat += '+1 EXTRA ROLL\n'
            self.nudges_left += self.combo_count
            self.bonus_stat += f'+{self.combo_count} NUDGES\n'
        if self.combo_count <= 0:
            self.last_appeared_words = []

    #  communication with the outside world...
    def get_U_score(self):
        return self.U_score

    def get_M_score(self):
        return self.M_score

    def get_C_score(self):
        return self.C_score

    def get_total_score(self):
        return int(self.total_score)

    def get_player_ID(self):
        return self.player_id

    def get_selection(self):
        return ' • '.join(self.selection)

    def get_status(self):
        return self.status_disp

    def get_chances(self):
        return self.chances_left

    def get_rolls(self):
        return self.rolls

    def get_ochinchin_count(self):
        return self.ochinchin_count

    def get_word_count(self):
        return self.word_count

    def get_nugdes_left(self):
        return self.nudges_left

    def get_nudges(self):
        return self.nudges

    def get_score_adds(self):
        U_score_add = f'+{int(self.U_score_add)}' if self.U_score_add >= 0 else f'{int(self.U_score_add)}'
        M_score_add = f'+{int(self.M_score_add)}' if self.M_score_add >= 0 else f'{int(self.M_score_add)}'
        C_score_add = f'+{int(self.C_score_add)}' if self.C_score_add >= 0 else f'{int(self.C_score_add)}'
        return U_score_add, M_score_add, C_score_add