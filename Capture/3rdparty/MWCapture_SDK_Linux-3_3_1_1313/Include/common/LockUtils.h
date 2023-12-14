
#pragma once


class CMWLock
{
public:
	CMWLock() {
		InitializeCriticalSection(&m_cs);
	}

	virtual ~CMWLock() {
		DeleteCriticalSection(&m_cs);
	}

public:
	void Lock() {
		EnterCriticalSection(&m_cs);
	}

	void Unlock() {
		LeaveCriticalSection(&m_cs);
	}

	BOOL TryLock() {
		return TryEnterCriticalSection(&m_cs);
	}
protected:
	 CRITICAL_SECTION	m_cs;
};

class CMWAutoLock
{
public:
	CMWAutoLock(CMWLock & section) : m_section(section) 
	{
		m_section.Lock();
	}

	virtual ~CMWAutoLock() {
		m_section.Unlock();
	}

protected:
	CMWLock& m_section;
};

class CMWAutoUnLock
{
public:
	CMWAutoUnLock(CMWLock & section) : m_section(section) 
	{
		m_section.Unlock();
	}

	virtual ~CMWAutoUnLock() {
		m_section.Lock();
	}

protected:
	CMWLock& m_section;
};
