
select * from CHECKINGACCOUNT_V1 where transcode not in ('Withdrawal', 'Deposit' )
-- and notes like 'VÝB%'
 order by transid desc;
 
 
 select * from CHECKINGACCOUNT_V1 where transcode in ('Withdrawal', 'Deposit' )
 order by transid desc;
 
 
 select count(0), notes from CHECKINGACCOUNT_V1 where transcode not in ('Withdrawal', 'Deposit' )
  group by notes
 order by count(0) desc;
