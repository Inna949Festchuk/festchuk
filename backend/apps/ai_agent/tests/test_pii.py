"""
Unit tests for the PII masker (apps.ai_agent.services.pii).

Pure-function tests: no Django, no database, no network.
Run inside the backend container:
    docker compose -f docker-compose.dev.yml exec backend pytest apps/ai_agent/tests/ -q
"""
from apps.ai_agent.services.pii import luhn_valid, mask_pii


class TestLuhn:
    def test_valid_card(self):
        assert luhn_valid('4111111111111111')

    def test_invalid_card(self):
        assert not luhn_valid('4111111111111112')

    def test_amex_length(self):
        assert luhn_valid('378282246310005')


class TestEmail:
    def test_plain_email(self):
        masked, found = mask_pii('пишите на konstantin@example.ru')
        assert masked == 'пишите на [EMAIL]'
        assert found == ['email']

    def test_email_with_dots_and_plus(self):
        masked, _ = mask_pii('a.b+c@sub.domain.co')
        assert masked == '[EMAIL]'

    def test_no_email(self):
        masked, found = mask_pii('привет, мир')
        assert masked == 'привет, мир'
        assert found == []


class TestCard:
    def test_spaces(self):
        masked, found = mask_pii('карта 4111 1111 1111 1111')
        assert masked == 'карта [CARD]'
        assert found == ['card']

    def test_bare_16_digits(self):
        masked, _ = mask_pii('4111111111111111')
        assert masked == '[CARD]'

    def test_bad_luhn_stays(self):
        # 16 digits, Luhn-invalid — must not be masked
        text = '4111111111111112'
        masked, found = mask_pii(text)
        assert masked == text
        assert 'card' not in found

    def test_version_not_masked(self):
        masked, found = mask_pii('Next.js 14.2.0 и Django 5.0')
        assert masked == 'Next.js 14.2.0 и Django 5.0'
        assert found == []

    def test_port_not_masked(self):
        masked, found = mask_pii('слушает на порту 8000')
        assert masked == 'слушает на порту 8000'
        assert found == []


class TestPhone:
    def test_plus7_spaced(self):
        masked, found = mask_pii('звони +7 999 123-45-67')
        assert masked == 'звони [PHONE]'
        assert found == ['phone']

    def test_bare_11_digits(self):
        masked, _ = mask_pii('89991234567')
        assert masked == '[PHONE]'

    def test_parens_format(self):
        masked, _ = mask_pii('тел: 8 (999) 123-45-67')
        assert masked == 'тел: [PHONE]'

    def test_toll_free_stays(self):
        # 8-800 numbers are corporate, not personal — keep them
        text = '8 800 555-35-35'
        masked, found = mask_pii(text)
        assert masked == text
        assert 'phone' not in found

    def test_date_not_masked(self):
        masked, found = mask_pii('дата 21.11.2026')
        assert masked == 'дата 21.11.2026'
        assert found == []


class TestPassport:
    def test_context_ru(self):
        masked, found = mask_pii('паспорт: серия 1234 номер 567890')
        assert masked == 'паспорт: [PASSPORT]'
        assert found == ['passport']

    def test_bare(self):
        masked, _ = mask_pii('1234 567890')
        assert masked == '[PASSPORT]'


class TestSnils:
    def test_valid_checksum(self):
        # 123-456-789, control digit 5 (375 % 100 = 75 -> 5)
        masked, found = mask_pii('СНИЛС 123-456-789 50')
        assert masked == 'СНИЛС [SNILS]'
        assert found == ['snils']

    def test_bad_checksum_stays(self):
        text = '123-456-789 40'
        masked, found = mask_pii(text)
        assert masked == text
        assert 'snils' not in found


class TestInn:
    def test_valid_10(self):
        # 770708389, control digit 3 (267 % 11 = 3)
        masked, found = mask_pii('ИНН 7707083893')
        assert masked == 'ИНН [INN]'
        assert found == ['inn']

    def test_valid_12(self):
        # 5001007322, control digits 5 and 1
        masked, _ = mask_pii('500100732251')
        assert masked == '[INN]'

    def test_bad_checksum_stays(self):
        text = '7707083894'
        masked, found = mask_pii(text)
        assert masked == text
        assert 'inn' not in found


class TestMixed:
    def test_phone_and_email(self):
        masked, found = mask_pii('моя почта a@b.ru, телефон +7 999 123-45-67')
        assert '[EMAIL]' in masked and '[PHONE]' in masked
        assert set(found) == {'email', 'phone'}

    def test_idempotent_on_placeholders(self):
        text, _ = mask_pii('8 800 555-35-35 и +7 999 123-45-67')
        again, found = mask_pii(text)
        assert again == text
        assert found == []

    def test_empty(self):
        masked, found = mask_pii('')
        assert masked == ''
        assert found == []
