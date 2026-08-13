#ifndef __STRING_UTILS_H__
#define __STRING_UTILS_H__

class CAutoConvertString
{
public:
	CAutoConvertString(const WCHAR *pwszString, UINT uCodePage = CP_ACP) {
		m_pwszString = const_cast<WCHAR *>(pwszString);
		m_pszString = NULL;
		m_pvAlloc = NULL;
		m_uCodePage = uCodePage;
	}

	CAutoConvertString(const char *pszString, UINT uCodePage = CP_ACP) {
		m_pszString = const_cast<char *>(pszString);
		m_pwszString = NULL;
		m_pvAlloc = NULL;
		m_uCodePage = uCodePage;
	}

	virtual ~CAutoConvertString() {
		if (NULL != m_pvAlloc) {
			free(m_pvAlloc);
			m_pvAlloc = NULL;
		}
	}

public:
	void Detach() {
		m_pszString = NULL;
		m_pwszString = NULL;
		m_pvAlloc = NULL;
	}

public:
	operator char *() {
		if (NULL == m_pszString) {
			int nLen = WideCharToMultiByte(m_uCodePage, 0, m_pwszString, -1, 
				NULL, 0, NULL, NULL);
			if (nLen == 0)
				return NULL;

			m_pszString = (char *)malloc(nLen);
			WideCharToMultiByte(m_uCodePage, 0, m_pwszString, -1, 
				m_pszString, nLen, NULL, NULL);

			m_pvAlloc = m_pszString;
		}

		return m_pszString;
	}

	operator WCHAR *() {
		if (NULL == m_pwszString) {
			int nLen = MultiByteToWideChar(m_uCodePage, 0, m_pszString, -1, 
				NULL, 0);
			if (nLen == 0)
				return NULL;

			m_pwszString = (WCHAR *)malloc(nLen * sizeof(WCHAR));
			MultiByteToWideChar(m_uCodePage, 0, m_pszString, -1, m_pwszString, nLen);

			m_pvAlloc = m_pwszString;
		}

		return m_pwszString;
	}

protected:
	WCHAR *	m_pwszString;
	char *	m_pszString;
	void *	m_pvAlloc;
	UINT	m_uCodePage;
};

#endif //__STRING_UTILS_H__